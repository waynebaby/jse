"""JSE execution engine."""

from pyjse.env import Env
from pyjse.sql import QUERY_FIELDS, pattern_to_triple, triple_to_sql_condition
from pyjse.types import JseValue


def _is_symbol(s: object) -> bool:
    return isinstance(s, str) and s.startswith("$") and not s.startswith("$$")


def _unescape(s: str) -> str:
    if s.startswith("$$"):
        return s[1:]
    return s


def _get_s_expr_key(obj: dict) -> str | None:
    dollar_keys = [k for k in obj if k.startswith("$") and not k.startswith("$$")]
    return dollar_keys[0] if len(dollar_keys) == 1 else None


class Engine:
    """JSE expression interpreter."""

    def __init__(self, env: Env) -> None:
        self.env = env

    def execute(self, expr: JseValue) -> JseValue:
        if expr is None or isinstance(expr, (int, float, bool)):
            return expr
        if isinstance(expr, str):
            return _unescape(expr)

        if isinstance(expr, list):
            if not expr:
                return expr
            first = expr[0]
            if isinstance(first, str) and _is_symbol(first):
                return self._eval_s_expr(first, expr[1:])
            return [self.execute(e) for e in expr]

        if isinstance(expr, dict):
            sym = _get_s_expr_key(expr)
            if sym:
                tail = expr[sym]
                args = [tail] if sym == "$expr" else (tail if isinstance(tail, list) else [tail])
                return self._eval_s_expr(sym, args)
            return {_unescape(k): self.execute(v) for k, v in expr.items()}

        return expr

    def _eval_s_expr(self, symbol: str, args: list) -> JseValue:
        if symbol == "$quote":
            return args[0] if args else None

        evaluated = [self.execute(a) for a in args]

        if symbol == "$and":
            return all(bool(v) for v in evaluated)
        if symbol == "$or":
            return any(bool(v) for v in evaluated)
        if symbol == "$not":
            return not bool(evaluated[0]) if evaluated else True

        if symbol == "$expr":
            return evaluated[0] if evaluated else None

        if symbol == "$pattern":
            if len(evaluated) < 3:
                raise ValueError("$pattern requires (subject, predicate, object)")
            subj, pred, obj = evaluated[0], evaluated[1], evaluated[2]
            if not all(isinstance(x, str) for x in (subj, pred, obj)):
                raise ValueError("$pattern requires string arguments")
            triple = pattern_to_triple(subj, pred, obj)
            cond = triple_to_sql_condition(triple)
            return (
                "select \n    subject, predicate, object, meta \n"
                f"from statement as s \nwhere {cond} \noffset 0\nlimit 100 \n"
            )

        if symbol == "$query":
            if len(evaluated) < 2 or not isinstance(evaluated[1], list):
                raise ValueError("$query expects [op, patterns array]")
            conditions = []
            for sql in evaluated[1]:
                if not isinstance(sql, str):
                    raise ValueError("Pattern must evaluate to SQL string")
                import re
                m = re.search(r"where\s+(.+?)\s+offset", sql, re.DOTALL | re.IGNORECASE)
                conditions.append(f"({m.group(1).strip()})" if m else sql)
            where = " and \n    ".join(conditions)
            return (
                f"select {QUERY_FIELDS} \nfrom statement \nwhere \n    {where} \n"
                "offset 0\nlimit 100 \n"
            )

        resolved = self.env.resolve(symbol)
        if resolved is not None:
            return resolved
        raise ValueError(f"Unknown symbol: {symbol}")

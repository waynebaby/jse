"""SQL extension functors for JSE.

Migrated from the original engine.py implementation:
- $pattern: Generate SQL for triple pattern matching
- $query: Generate SQL for multi-pattern queries
"""

import re
from typing import Callable, TYPE_CHECKING
from pyjse.types import JseValue
from pyjse.sql import pattern_to_triple, triple_to_sql_condition, QUERY_FIELDS

if TYPE_CHECKING:
    from pyjse.env import Env


# Type alias for functors
Functor = Callable[['Env', ...], JseValue]


def _pattern(env: 'Env', *args: JseValue) -> JseValue:
    """Generate SQL for triple pattern matching.

    Form: [$pattern, subject, predicate, object]

    Args:
        env: Environment
        *args: (subject, predicate, object) - all must be strings

    Returns:
        SQL query string

    Raises:
        ValueError: If wrong arguments or non-string types
    """
    if len(args) < 3:
        raise ValueError("$pattern requires (subject, predicate, object)")

    subj = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    pred = env.eval(args[1]) if hasattr(env, 'eval') else args[1]
    obj = env.eval(args[2]) if hasattr(env, 'eval') else args[2]

    if not all(isinstance(x, str) for x in (subj, pred, obj)):
        raise ValueError("$pattern requires string arguments")

    triple = pattern_to_triple(subj, pred, obj)
    cond = triple_to_sql_condition(triple)

    return (
        "select \n    subject, predicate, object, meta \n"
        f"from statement as s \nwhere {cond} \noffset 0\nlimit 100 \n"
    )


def _query(env: 'Env', *args: JseValue) -> JseValue:
    """Generate SQL for multi-pattern query.

    Form: [$query, op, patterns]
    where patterns is a list of SQL strings from $pattern

    Args:
        env: Environment
        *args: (op, patterns) arguments

    Returns:
        Combined SQL query string

    Raises:
        ValueError: If wrong arguments or invalid patterns
    """
    if len(args) < 2:
        raise ValueError("$query expects [op, patterns array]")

    # First arg is operator (currently ignored, assumes "and")
    op = env.eval(args[0]) if hasattr(env, 'eval') else args[0]
    patterns = env.eval(args[1]) if hasattr(env, 'eval') else args[1]

    if not isinstance(patterns, list):
        raise ValueError("$query second argument must be a list")

    conditions = []
    for sql in patterns:
        if not isinstance(sql, str):
            raise ValueError("Pattern must evaluate to SQL string")
        m = re.search(r"where\s+(.+?)\s+offset", sql, re.DOTALL | re.IGNORECASE)
        if m:
            conditions.append(f"({m.group(1).strip()})")
        else:
            conditions.append(f"({sql})")

    where = " and \n    ".join(conditions)
    return (
        f"select {QUERY_FIELDS} \nfrom statement \nwhere \n    {where} \n"
        "offset 0\nlimit 100 \n"
    )


# Dict of all SQL functors for registration
SQL_FUNCTORS: dict[str, Functor] = {
    "$pattern": _pattern,
    "$query": _query,
}

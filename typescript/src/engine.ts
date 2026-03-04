import type { Env } from "./env.js";
import type { JseValue } from "./types.js";
import {
  QUERY_FIELDS,
  patternToTriple,
  tripleToSqlCondition,
} from "./sql.js";

function isSymbol(s: unknown): s is string {
  return typeof s === "string" && s.startsWith("$") && !s.startsWith("$$");
}

function unescapeSymbol(s: string): string {
  if (s.startsWith("$$")) {
    return s.slice(1);
  }
  return s;
}

function getSExprKey(obj: Record<string, JseValue>): string | null {
  const dollarKeys = Object.keys(obj).filter((k) => k.startsWith("$") && !k.startsWith("$$"));
  if (dollarKeys.length === 1) {
    return dollarKeys[0];
  }
  return null;
}

export class Engine {
  constructor(private env: Env) {}

  execute(expr: JseValue): JseValue {
    // literals
    if (expr === null || typeof expr === "number" || typeof expr === "boolean") {
      return expr;
    }
    if (typeof expr === "string") {
      return unescapeSymbol(expr);
    }

    // array: s-expression if first element is symbol
    if (Array.isArray(expr)) {
      if (expr.length === 0) return expr;
      const first = expr[0];
      if (typeof first === "string" && isSymbol(first)) {
        return this.evalSExpr(first, expr.slice(1));
      }
      return expr.map((e) => this.execute(e));
    }

    // object
    if (typeof expr === "object") {
      const sym = getSExprKey(expr as Record<string, JseValue>);
      if (sym) {
        const tail = (expr as Record<string, JseValue>)[sym];
        // $expr takes the whole value as single expression to evaluate
        const args = sym === "$expr" ? [tail] : Array.isArray(tail) ? tail : [tail];
        return this.evalSExpr(sym, args);
      }
      // plain object
      const result: Record<string, JseValue> = {};
      for (const [k, v] of Object.entries(expr)) {
        result[unescapeSymbol(k)] = this.execute(v);
      }
      return result;
    }

    return expr;
  }

  private evalSExpr(symbol: string, args: JseValue[]): JseValue {
    // $quote: do not evaluate the argument
    if (symbol === "$quote") {
      return args[0] ?? null;
    }

    const evaluated = args.map((a) => this.execute(a));

    switch (symbol) {

      case "$and":
        return evaluated.every((v) => Boolean(v));

      case "$or":
        return evaluated.some((v) => Boolean(v));

      case "$not":
        return !Boolean(evaluated[0]);

      case "$expr":
        return evaluated[0] ?? null;

      case "$pattern": {
        const [subj, pred, obj] = evaluated;
        if (
          typeof subj !== "string" ||
          typeof pred !== "string" ||
          typeof obj !== "string"
        ) {
          throw new Error("$pattern requires (subject, predicate, object) strings");
        }
        const triple = patternToTriple(subj, pred, obj);
        const cond = tripleToSqlCondition(triple);
        return `select \n    subject, predicate, object, meta \nfrom statement as s \nwhere ${cond} \noffset 0\nlimit 100 \n`;
      }

      case "$query": {
        const [_op, patternResults] = evaluated;
        if (!Array.isArray(patternResults)) {
          throw new Error("$query expects [op, patterns array]");
        }
        const conditions: string[] = [];
        for (const sql of patternResults) {
          if (typeof sql !== "string") throw new Error("Pattern must evaluate to SQL string");
          const match = sql.match(/where\s+(.+?)\s+offset/is);
          conditions.push(match ? `(${match[1].trim()})` : sql);
        }
        const whereClause = conditions.join(" and \n    ");
        return `select ${QUERY_FIELDS} \nfrom statement \nwhere \n    ${whereClause} \noffset 0\nlimit 100 \n`;
      }

      default:
        const resolved = this.env.resolve?.(symbol);
        if (resolved !== undefined) return resolved;
        throw new Error(`Unknown symbol: ${symbol}`);
    }
  }
}

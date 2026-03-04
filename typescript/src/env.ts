import type { JseValue } from "./types.js";

/**
 * Base environment for JSE execution.
 * Can be extended to mount knowledge/statement data.
 */
export interface Env {
  /** Optional: resolve symbol to value */
  resolve?(symbol: string): JseValue | undefined;
}

/**
 * Expression-only environment for basic and logic evaluation.
 * No query/SQL capabilities.
 */
export class ExpressionEnv implements Env {
  resolve(_symbol: string): JseValue | undefined {
    return undefined;
  }
}

/**
 * Environment for JSE execution.
 *
 * Follows the design in docs/regular.md:
 * - env has nullable parent field for scope chain lookup
 * - env provides register() method for def/defn
 * - env provides load() method for functor modules
 * - env.eval() delegates to ast.apply() (following jisp pattern)
 */

import type { JseValue, AstNodeLike } from "./types.js";

/**
 * Environment for JSE execution with scope chaining.
 */
export class Env {
  private _parent: Env | null;
  private _bindings: Map<string, JseValue>;
  private _currentMeta: Record<string, JseValue>;

  constructor(parent: Env | null = null) {
    this._parent = parent;
    this._bindings = new Map();
    this._currentMeta = {};
  }

  /**
   * Get parent environment.
   */
  getParent(): Env | null {
    return this._parent;
  }

  /**
   * Get current metadata context.
   */
  getMeta(): Record<string, JseValue> {
    return this._currentMeta;
  }

  /**
   * Set current metadata context (before functor call).
   */
  setMeta(meta: Record<string, JseValue>): void {
    this._currentMeta = meta;
  }

  /**
   * Clear current metadata context (after functor call).
   */
  clearMeta(): void {
    this._currentMeta = {};
  }

  /**
   * Resolve symbol to value by searching up the scope chain.
   * If symbol is not found in current environment, searches parent.
   * Returns undefined if symbol is not found anywhere in the chain.
   */
  resolve(symbol: string): JseValue | undefined {
    if (this._bindings.has(symbol)) {
      return this._bindings.get(symbol);
    }
    if (this._parent) {
      return this._parent.resolve(symbol);
    }
    return undefined;
  }

  /**
   * Register a new symbol binding in the current environment.
   * Throws if symbol already exists in current scope.
   * Used by $def and $defn operators.
   */
  register(name: string, value: JseValue): void {
    if (this._bindings.has(name)) {
      throw new Error(`Symbol '${name}' already exists in current scope`);
    }
    this._bindings.set(name, value);
  }

  /**
   * Set a symbol binding, overwriting if exists.
   * Unlike register(), this allows overwriting existing bindings.
   */
  set(name: string, value: JseValue): void {
    this._bindings.set(name, value);
  }

  /**
   * Check if symbol exists in current or parent scopes.
   */
  exists(name: string): boolean {
    if (this._bindings.has(name)) {
      return true;
    }
    if (this._parent) {
      return this._parent.exists(name);
    }
    return false;
  }

  /**
   * Evaluate an expression in this environment.
   * If expr is an AstNode, delegates to expr.apply(this).
   * Otherwise returns expr as-is (for primitive values).
   *
   * This follows the jisp pattern where env.eval() delegates to ast.apply().
   */
  eval(expr: JseValue): JseValue {
    // Check if it's an AstNode by checking for apply method
    if (
      typeof expr === "object" &&
      expr !== null &&
      "apply" in expr &&
      typeof (expr as AstNodeLike).apply === "function"
    ) {
      // This is an AstNode - delegate to its apply method
      return (expr as AstNodeLike).apply(this);
    }
    // Primitive value - return as-is
    return expr;
  }

  /**
   * Load functor module(s) into this environment.
   *
   * @param modules - One or more dictionaries of functor names and their implementations
   */
  load(...modules: Record<string, (env: Env, ...args: JseValue[]) => JseValue>[]): void {
    for (const module of modules) {
      for (const [name, functor] of Object.entries(module)) {
        this.register(name, functor);
      }
    }
  }
}

/**
 * Base environment interface for compatibility.
 * @deprecated Use Env class directly.
 */
export interface IEnv {
  resolve?(symbol: string): JseValue | undefined;
}

/**
 * Expression-only environment for basic and logic evaluation.
 * Can be extended to mount knowledge/statement data.
 */
export class ExpressionEnv extends Env implements IEnv {
  override resolve(_symbol: string): JseValue | undefined {
    return undefined;
  }
}

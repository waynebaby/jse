/**
 * JSE (JSON Structural Expression) value types.
 * - JSON primitives and structures
 * - $symbol strings (escape: $$)
 * - $quote for pass-through
 */
export type JseValue =
  | number
  | string
  | boolean
  | null
  | JseValue[]
  | { [key: string]: JseValue };

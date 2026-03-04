import { describe, it, expect } from "vitest";
import { Engine, ExpressionEnv } from "../index.js";

function createEngine() {
  return new Engine(new ExpressionEnv());
}

describe("basic expressions", () => {
  const engine = createEngine();

  it("number", () => {
    expect(engine.execute(42)).toBe(42);
  });

  it("float", () => {
    expect(engine.execute(3.14)).toBe(3.14);
  });

  it("string", () => {
    expect(engine.execute("hello")).toBe("hello");
  });

  it("boolean", () => {
    expect(engine.execute(true)).toBe(true);
    expect(engine.execute(false)).toBe(false);
  });

  it("null", () => {
    expect(engine.execute(null)).toBe(null);
  });

  it("array", () => {
    const result = engine.execute([1, 2, 3]);
    expect(Array.isArray(result)).toBe(true);
    expect(result).toEqual([1, 2, 3]);
  });

  it("object", () => {
    const result = engine.execute({ a: 1, b: "x" }) as Record<string, unknown>;
    expect(typeof result).toBe("object");
    expect(result).toEqual({ a: 1, b: "x" });
  });
});

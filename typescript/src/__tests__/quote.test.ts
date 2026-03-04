import { describe, it, expect } from "vitest";
import { Engine, ExpressionEnv } from "../index.js";

function createEngine() {
  return new Engine(new ExpressionEnv());
}

describe("$quote and $$ escape", () => {
  const engine = createEngine();

  it("$quote passes through without evaluation", () => {
    const expr = ["$quote", { $foo: "bar", data: [1, 2, 3] }];
    const result = engine.execute(expr) as Record<string, unknown>;
    expect(result).toEqual({ $foo: "bar", data: [1, 2, 3] });
  });

  it("$$ escapes $ in strings", () => {
    const result = engine.execute("$$expr") as string;
    expect(result).toBe("$expr");
  });
});

import { describe, it, expect } from "vitest";
import { Engine, ExpressionEnv } from "../index.js";

function createEngine() {
  return new Engine(new ExpressionEnv());
}

describe("logic expressions", () => {
  const engine = createEngine();

  it("$and basic", () => {
    expect(engine.execute(["$and", true, true, true])).toBe(true);
    expect(engine.execute(["$and", true, false, true])).toBe(false);
  });

  it("$or basic", () => {
    expect(engine.execute(["$or", false, false, true])).toBe(true);
    expect(engine.execute(["$or", false, false, false])).toBe(false);
  });

  it("$not basic", () => {
    expect(engine.execute(["$not", true])).toBe(false);
    expect(engine.execute(["$not", false])).toBe(true);
  });

  it("nested logic", () => {
    const expr = [
      "$or",
      ["$and", true, ["$not", false]],
      ["$and", false, true],
    ];
    expect(engine.execute(expr)).toBe(true);
  });

  it("deep nesting", () => {
    const expr = [
      "$not",
      [
        "$or",
        ["$and", false, ["$not", false]],
        ["$not", true],
      ],
    ];
    expect(engine.execute(expr)).toBe(true);
  });
});

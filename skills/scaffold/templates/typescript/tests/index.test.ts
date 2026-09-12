import { describe, expect, it } from "vitest";
import { main } from "../src/index.js";

describe("main", () => {
  it("runs without throwing", () => {
    expect(() => main()).not.toThrow();
  });
});

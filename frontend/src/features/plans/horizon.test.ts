import { describe, expect, it } from "vitest";
import { horizonYears } from "./schema";

describe("horizonYears", () => {
  it("follows the loan term like the backend", () => {
    expect(horizonYears(36)).toBe(3);
    expect(horizonYears(30)).toBe(3);
    expect(horizonYears(12)).toBe(1);
    expect(horizonYears(1)).toBe(1);
    expect(horizonYears(120)).toBe(10);
    expect(horizonYears(180)).toBe(10);
    expect(horizonYears(undefined)).toBe(10);
  });
});

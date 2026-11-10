import { describe, expect, it } from "vitest";
import { safeNextPath } from "./safe-next";

describe("safeNextPath", () => {
  it("keeps internal paths with query", () => {
    expect(safeNextPath("/dashboard/")).toBe("/dashboard/");
    expect(safeNextPath("/reja/?id=abc")).toBe("/reja/?id=abc");
  });

  it.each([
    null, "", "dashboard", "https://evil.com", "//evil.com", "/\\evil.com", "/a\\b", "/x\nLocation: y",
    "/kirish/", "/royxat?next=/x", "/" + "a".repeat(600),
  ])("falls back for %j", (value) => {
    expect(safeNextPath(value)).toBe("/kabinet/");
  });
});

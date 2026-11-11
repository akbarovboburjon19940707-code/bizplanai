import { describe, expect, it } from "vitest";
import { pollDelay } from "./poll";

describe("pollDelay", () => {
  it("polls Click/Payme fast while pending", () => {
    expect(pollDelay("pending", "click")).toBe(3000);
    expect(pollDelay("pending", "payme")).toBe(3000);
  });
  it("waits for the receipt on manual pending, then polls slowly while reviewing", () => {
    expect(pollDelay("pending", "manual")).toBe(0);
    expect(pollDelay("reviewing", "manual")).toBe(15000);
  });
  it.each(["paid", "cancelled", "rejected"])("stops on %s", (s) => expect(pollDelay(s, "click")).toBe(0));
});

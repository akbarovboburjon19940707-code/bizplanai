import { describe, expect, it } from "vitest";
import { formatLocalPhone, formatPhone, isCompletePhone, phoneDigits, toE164 } from "./phone";

describe("phone", () => {
  it("formats while typing", () => {
    expect(formatPhone("9")).toBe("+998 9");
    expect(formatPhone("90123")).toBe("+998 90 123");
    expect(formatPhone("901234567")).toBe("+998 90 123 45 67");
  });

  it("accepts pasted numbers with country code", () => {
    expect(phoneDigits("+998 (90) 123-45-67")).toBe("901234567");
    expect(phoneDigits("998901234567")).toBe("901234567");
    expect(toE164("90 123 45 67")).toBe("+998901234567");
  });

  it("re-formatting a formatted value is stable", () => {
    const once = formatPhone("901234567");
    expect(formatPhone(once)).toBe(once);
    expect(formatPhone("+998 9")).toBe("+998 9");
    expect(formatLocalPhone(formatLocalPhone("901234567"))).toBe("90 123 45 67");
  });

  it("input mask keeps only the local part", () => {
    expect(formatLocalPhone("90")).toBe("90");
    expect(formatLocalPhone("+998901234567")).toBe("90 123 45 67");
    expect(formatLocalPhone("99 812 34 56")).toBe("99 812 34 56"); // 99 operator kodi, 998 emas
  });

  it("does not treat a short local number starting with 998 as a country code", () => {
    expect(phoneDigits("998")).toBe("998");
  });

  it("checks completeness and caps length", () => {
    expect(isCompletePhone("+998 90 123 45 6")).toBe(false);
    expect(isCompletePhone("+998 90 123 45 67")).toBe(true);
    expect(phoneDigits("9012345678999")).toBe("901234567");
  });
});

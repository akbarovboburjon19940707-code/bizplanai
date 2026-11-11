import { describe, expect, it } from "vitest";
import { MAX_RECEIPT_BYTES, checkReceipt } from "./receipt";
import { isTrustedCheckoutUrl } from "./types";

describe("checkReceipt", () => {
  it("accepts images and pdf up to 10 MB", () => {
    expect(checkReceipt({ name: "a.jpg", type: "image/jpeg", size: 1000 })).toBeNull();
    expect(checkReceipt({ name: "a.pdf", type: "application/pdf", size: MAX_RECEIPT_BYTES })).toBeNull();
    expect(checkReceipt({ name: "scan.webp", type: "", size: 10 })).toBeNull();
  });
  it("rejects other types and big files", () => {
    expect(checkReceipt({ name: "a.heic", type: "image/heic", size: 10 })).toBe("badType");
    expect(checkReceipt({ name: "a.exe", type: "", size: 10 })).toBe("badType");
    expect(checkReceipt({ name: "a.png", type: "image/png", size: MAX_RECEIPT_BYTES + 1 })).toBe("tooLarge");
  });
});

describe("isTrustedCheckoutUrl", () => {
  it.each([
    ["https://my.click.uz/services/pay?x=1", true],
    ["https://checkout.paycom.uz/abc", true],
    ["https://evil.com/?https://my.click.uz", false],
    ["https://click.uz.evil.com/", false],
    ["http://my.click.uz/", false],
    ["javascript:alert(1)", false],
  ])("%s -> %s", (url, ok) => expect(isTrustedCheckoutUrl(url)).toBe(ok));
});

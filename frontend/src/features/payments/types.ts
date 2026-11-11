import type { components } from "@/shared/api/schema";

export type PaymentOut = components["schemas"]["PaymentOut"];
export type PaymentKind = "subscription" | "catalog" | "plan_credit";
export type Provider = "click" | "payme" | "manual";
export const PROVIDERS: readonly Provider[] = ["click", "payme", "manual"];

export type ManualCheckout = {
  type: "manual";
  card_number: string;
  card_holder: string;
  amount_som: number;
  instructions: string;
};
export type Checkout = { type: "redirect"; url: string } | ManualCheckout | Record<string, never>;
export type PaymentEnvelope = { payment: PaymentOut; checkout: Checkout };

export function isManual(c: Checkout | undefined): c is ManualCheckout {
  return !!c && "type" in c && c.type === "manual";
}

/** Click/Payme manzili faqat ularning domenlari bo'lsa ochiladi (API buzilgan bo'lsa ham boshqa saytga ketmaydi). */
export function isTrustedCheckoutUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === "https:" && /(^|\.)(click\.uz|paycom\.uz|payme\.uz)$/.test(u.hostname);
  } catch {
    return false;
  }
}

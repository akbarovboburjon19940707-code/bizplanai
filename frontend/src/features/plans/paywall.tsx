"use client";

import Link from "next/link";
import { useState } from "react";
import { PaymentDialog } from "@/features/payments/payment-dialog";
import { uz } from "@/messages/uz";
import { useApi } from "@/shared/api/use-api";
import { formatSom } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";

const t = uz.plans.result;

/** Bepul foydalanuvchi: hisob-kitob ekranda tayyor, hujjat uchun to'lov (bitta reja yoki tarif). */
export function Paywall() {
  const pricing = useApi<{ plan_credit_price_som: number }>("/v1/pricing");
  const [open, setOpen] = useState(false);
  const price = pricing.data?.plan_credit_price_som;
  return (
    <section aria-labelledby="paywall-title" className="mt-6 rounded-card border border-brand/30 bg-blue-50/60 p-5">
      <h2 id="paywall-title" className="font-[var(--font-outfit)] text-lg font-bold text-ink">{t.paywallTitle}</h2>
      <p className="mt-1 text-sm text-ink">{t.paywallText}</p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button type="button" size="lg" onClick={() => setOpen(true)} disabled={price === undefined}>
          {price === undefined ? t.creating : t.buySingle(formatSom(price))}
        </Button>
        <Button asChild variant="outline" size="lg">
          <Link href="/tariflar/">{t.tariffs}</Link>
        </Button>
      </div>
      <p className="mt-3 text-xs text-muted">{t.paidHint}</p>
      <PaymentDialog open={open} onClose={() => setOpen(false)} kind="plan_credit" title={t.singleTitle} />
    </section>
  );
}

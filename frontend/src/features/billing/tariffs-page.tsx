"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/features/auth/auth-context";
import { PaymentDialog } from "@/features/payments/payment-dialog";
import { useBuy } from "@/features/payments/use-buy";
import { uz } from "@/messages/uz";
import { useApi } from "@/shared/api/use-api";
import type { components } from "@/shared/api/schema";
import { cn } from "@/shared/lib/cn";
import { formatNumber } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";

type Tariff = components["schemas"]["TariffOut"];
type MeOut = components["schemas"]["MeOut"];
type Pricing = components["schemas"]["PricingOut"];
const t = uz.tariffs;

function Feature({ ok, children }: { ok: boolean; children: string }) {
  return (
    <li className={cn("flex items-start gap-2 text-sm", ok ? "text-ink" : "text-muted line-through decoration-slate-300")}>
      <span aria-hidden="true" className={cn("mt-0.5 font-bold", ok ? "text-emerald-600" : "text-slate-300")}>{ok ? "✓" : "–"}</span>
      {children}
    </li>
  );
}

function TariffCard({ tariff, current, featured, onChoose }: {
  tariff: Tariff;
  current: boolean;
  featured: boolean;
  onChoose: () => void;
}) {
  const free = tariff.price_som <= 0;
  return (
    <article
      className={cn(
        "relative flex flex-col rounded-card border bg-white p-6 shadow-soft",
        featured ? "border-brand ring-2 ring-brand/20" : "border-border",
      )}
      aria-label={tariff.name}
    >
      {current ? (
        <span className="absolute right-4 top-4 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">{t.current}</span>
      ) : null}
      <h2 className="text-lg font-bold text-ink">{tariff.name}</h2>
      <p className="mt-3 flex items-baseline gap-1">
        <span className="font-[var(--font-outfit)] text-3xl font-bold tabular-nums text-ink">{formatNumber(tariff.price_som)}</span>
        <span className="text-sm text-muted">so‘m {free ? t.forever : t.perPeriod(tariff.duration_days)}</span>
      </p>
      <ul className="mt-5 flex flex-1 flex-col gap-2.5">
        <Feature ok>{t.daily(tariff.daily_limit)}</Feature>
        <Feature ok>{t.monthly(tariff.monthly_limit)}</Feature>
        <Feature ok>{t.word}</Feature>
        <Feature ok={tariff.ai_enabled}>{tariff.ai_enabled ? t.ai : t.noAi}</Feature>
      </ul>
      <div className="mt-6">
        {free ? (
          <Button asChild variant="outline" className="w-full"><Link href="/dashboard/">{t.start}</Link></Button>
        ) : (
          <Button type="button" variant={featured ? "primary" : "outline"} className="w-full" onClick={onChoose}>
            {t.choose}
          </Button>
        )}
      </div>
    </article>
  );
}

export function TariffsPage() {
  const tariffs = useApi<Tariff[]>("/v1/tariffs");
  const { status } = useAuth();
  const me = useApi<MeOut>(status === "authenticated" ? "/v1/me" : null);
  const buy = useBuy();
  const pricing = useApi<Pricing>("/v1/pricing");
  // Tanlangan mahsulot: tarif obunasi yoki bitta reja (plan_credit)
  const [chosen, setChosen] = useState<{ kind: "subscription" | "plan_credit"; targetId?: string; title: string } | null>(null);
  const list = [...(tariffs.data ?? [])].sort((a, b) => a.price_som - b.price_som);
  const featuredCode = list.filter((x) => x.price_som > 0)[0]?.code;

  return (
    <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="font-[var(--font-outfit)] text-3xl font-bold tracking-tight text-ink sm:text-4xl">{t.title}</h1>
        <p className="mt-3 text-muted">{t.subtitle}</p>
      </div>
      {tariffs.loading && !tariffs.data ? (
        <div className="mt-10 grid gap-6 md:grid-cols-3" aria-busy="true">
          {[0, 1, 2].map((i) => <div key={i} className="h-80 animate-pulse rounded-card bg-white" />)}
        </div>
      ) : tariffs.error ? (
        <p className="mt-10 text-center text-sm text-red-600">
          {tariffs.error.message || t.loadError}{" "}
          <button type="button" className="font-semibold text-brand hover:underline" onClick={tariffs.reload}>{uz.account.retry}</button>
        </p>
      ) : (
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {list.map((tariff) => (
            <TariffCard
              key={tariff.code}
              tariff={tariff}
              current={me.data?.subscription.tariff_code === tariff.code}
              featured={tariff.code === featuredCode}
              onChoose={() => {
                setChosen({ kind: "subscription", targetId: tariff.code, title: tariff.name });
                buy.start();
              }}
            />
          ))}
        </div>
      )}
      {pricing.data ? (
        <div className="mx-auto mt-8 flex max-w-3xl flex-col gap-4 rounded-card border border-border bg-white p-6 shadow-soft sm:flex-row sm:items-center">
          <div className="flex-1">
            <h2 className="text-lg font-bold text-ink">{t.single.title}</h2>
            <p className="mt-1 text-sm text-muted">{t.single.text}</p>
          </div>
          <p className="flex items-baseline gap-1 sm:text-right">
            <span className="font-[var(--font-outfit)] text-2xl font-bold tabular-nums text-ink">{formatNumber(pricing.data.plan_credit_price_som)}</span>
            <span className="text-sm text-muted">so‘m {t.single.perPlan}</span>
          </p>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setChosen({ kind: "plan_credit", title: t.single.title });
              buy.start();
            }}
          >
            {t.single.buy}
          </Button>
        </div>
      ) : null}
      <p className="mt-8 text-center text-sm text-muted">{t.quotaHint}</p>
      {chosen ? (
        <PaymentDialog open={buy.open} onClose={buy.close} kind={chosen.kind} targetId={chosen.targetId} title={chosen.title} />
      ) : null}
    </section>
  );
}

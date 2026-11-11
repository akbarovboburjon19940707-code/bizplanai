import Link from "next/link";
import type { Tariff } from "@/features/catalog/build-data";
import { ProductCard } from "@/features/catalog/product-card";
import type { Product } from "@/features/catalog/types";
import { uz } from "@/messages/uz";
import { formatNumber } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";

const t = uz.home;

function SectionTitle({ title, link }: { title: string; link?: { href: string; label: string } }) {
  return (
    <div className="flex items-end justify-between gap-4">
      <h2 className="font-[var(--font-outfit)] text-2xl font-bold tracking-tight text-ink sm:text-3xl">{title}</h2>
      {link ? <Link href={link.href} className="shrink-0 text-sm font-semibold text-brand hover:underline">{link.label}</Link> : null}
    </div>
  );
}

export function Steps() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8" aria-labelledby="steps">
      <h2 id="steps" className="font-[var(--font-outfit)] text-2xl font-bold tracking-tight text-ink sm:text-3xl">{t.stepsTitle}</h2>
      <ol className="mt-6 grid gap-5 md:grid-cols-3">
        {t.steps.map((s, i) => (
          <li key={s.title} className="rounded-card border border-border bg-white p-6 shadow-soft">
            <span className="grid size-9 place-items-center rounded-full bg-blue-50 text-sm font-bold text-brand">{i + 1}</span>
            <h3 className="mt-4 text-lg font-bold text-ink">{s.title}</h3>
            <p className="mt-1.5 text-sm leading-6 text-muted">{s.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function Features() {
  return (
    <section className="bg-white" aria-labelledby="features">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <h2 id="features" className="font-[var(--font-outfit)] text-2xl font-bold tracking-tight text-ink sm:text-3xl">{t.featuresTitle}</h2>
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {t.features.map((f) => (
            <div key={f.title} className="rounded-card bg-canvas p-5">
              <h3 className="font-bold text-ink">{f.title}</h3>
              <p className="mt-1.5 text-sm leading-6 text-muted">{f.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Popular({ products }: { products: Product[] }) {
  if (!products.length) return null;
  return (
    <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <SectionTitle title={t.popularTitle} link={{ href: "/katalog/", label: t.allCatalog }} />
      <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((p) => <ProductCard key={p.id} product={p} />)}
      </div>
    </section>
  );
}

export function TariffStrip({ tariffs }: { tariffs: Tariff[] }) {
  if (!tariffs.length) return null;
  const tt = uz.tariffs;
  return (
    <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <SectionTitle title={t.tariffsTitle} link={{ href: "/tariflar/", label: t.allTariffs }} />
      <div className="mt-6 grid gap-5 md:grid-cols-3">
        {tariffs.map((x) => (
          <div key={x.code} className="rounded-card border border-border bg-white p-6 shadow-soft">
            <h3 className="font-bold text-ink">{x.name}</h3>
            <p className="mt-2 flex items-baseline gap-1">
              <span className="text-2xl font-bold tabular-nums text-ink">{formatNumber(x.price_som)}</span>
              <span className="text-sm text-muted">so‘m {x.price_som > 0 ? tt.perPeriod(x.duration_days) : tt.forever}</span>
            </p>
            <p className="mt-3 text-sm text-muted">{tt.daily(x.daily_limit)} · {tt.monthly(x.monthly_limit)}</p>
            <p className="mt-1 text-sm text-muted">{x.ai_enabled ? tt.ai : tt.noAi}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function FinalCta() {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
      <div className="flex flex-col items-start gap-4 rounded-card bg-gradient-to-br from-slate-900 via-blue-900 to-blue-600 p-8 text-white sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-[var(--font-outfit)] text-2xl font-bold">{t.ctaTitle}</h2>
          <p className="mt-1 text-blue-100">{t.ctaText}</p>
        </div>
        <Button asChild size="lg" variant="outline" className="border-white/30 bg-white text-ink">
          <Link href="/dashboard/">{t.primaryAction}</Link>
        </Button>
      </div>
    </section>
  );
}

import Link from "next/link";
import type { Pricing, Tariff } from "@/features/catalog/build-data";
import { ProductCard } from "@/features/catalog/product-card";
import type { Category, Product } from "@/features/catalog/types";
import { uz } from "@/messages/uz";
import { cn } from "@/shared/lib/cn";
import { formatNumber } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";

const t = uz.home;
const tt = uz.tariffs;
const h2 = "font-[var(--font-outfit)] text-3xl font-bold tracking-tight text-ink sm:text-4xl";
const eyebrow = "text-sm font-semibold uppercase tracking-wider text-brand";

export function StatsBar({ plans }: { plans: number }) {
  return (
    <section className="border-y border-border bg-white" aria-label={uz.appName}>
      <dl className="mx-auto grid max-w-7xl grid-cols-2 gap-6 px-4 py-8 sm:px-6 md:grid-cols-4 lg:px-8">
        {t.stats(plans).map((s) => (
          <div key={s.label} className="flex flex-col-reverse justify-end">
            <dt className="text-sm text-muted">{s.label}</dt>
            <dd className="font-[var(--font-outfit)] text-2xl font-bold text-ink sm:text-3xl">{s.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export function DocumentContents() {
  return (
    <section className="bg-white" aria-labelledby="contents">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <div className="max-w-2xl">
          <p className={eyebrow}>{t.contentsEyebrow}</p>
          <h2 id="contents" className={cn(h2, "mt-2")}>{t.contentsTitle}</h2>
          <p className="mt-3 text-muted">{t.contentsText}</p>
        </div>
        <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {t.contents.map((c) => (
            <li key={c.title} className="flex gap-4 rounded-2xl border border-border p-5 sm:block sm:p-6">
              <span aria-hidden="true" className="grid size-10 shrink-0 place-items-center rounded-xl bg-blue-50 text-lg">{c.icon}</span>
              <div>
                <h3 className="font-semibold text-ink sm:mt-4">{c.title}</h3>
                <p className="mt-1 text-sm leading-6 text-muted sm:mt-1.5">{c.text}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function Steps() {
  return (
    <section className="bg-canvas" aria-labelledby="steps">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 id="steps" className={cn(h2, "text-center")}>{t.stepsTitle}</h2>
        <ol className="relative mt-12 grid gap-10 md:grid-cols-3 md:gap-8">
          <li aria-hidden="true" className="absolute left-[16%] right-[16%] top-6 hidden h-0.5 bg-gradient-to-r from-brand/20 via-brand/50 to-brand/20 md:block" />
          {t.steps.map((s, i) => (
            <li key={s.title} className="relative text-center">
              <span className={cn("mx-auto grid size-12 place-items-center rounded-full font-[var(--font-outfit)] text-lg font-bold text-white ring-8 ring-canvas",
                i === t.steps.length - 1 ? "bg-emerald-600" : "bg-brand")}>{i + 1}</span>
              <h3 className="mt-5 font-semibold text-ink">{s.title}</h3>
              <p className="mx-auto mt-2 max-w-xs text-sm leading-6 text-muted">{s.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function Popular({ products, categories, total }: { products: Product[]; categories: Category[]; total: number }) {
  if (!products.length) return null;
  const top = [...categories].sort((a, b) => b.count - a.count).slice(0, 5);
  const chip = "rounded-full border px-3.5 py-1.5 text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand";
  return (
    <section className="bg-white" aria-labelledby="popular">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className={eyebrow}>{t.popularEyebrow}</p>
            <h2 id="popular" className={cn(h2, "mt-2")}>{t.popularTitle}</h2>
          </div>
          <Link href="/katalog/" className="text-sm font-semibold text-brand hover:underline">{t.allCatalog(total)}</Link>
        </div>
        {top.length ? (
          <ul className="mt-6 flex flex-wrap gap-2">
            <li><Link href="/katalog/" className={cn(chip, "border-ink bg-ink font-semibold text-white")}>{t.allCategories}</Link></li>
            {top.map((c) => (
              <li key={c.key}>
                <Link href={`/katalog/?category=${c.key}`} className={cn(chip, "border-border text-ink hover:border-blue-200 hover:text-brand")}>
                  <span aria-hidden="true">{c.icon}</span> {c.label}
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {products.map((p) => <ProductCard key={p.id} product={p} />)}
        </div>
      </div>
    </section>
  );
}

function PriceCard({ title, price, unit, features, featured }: {
  title: string; price: number; unit: string; features: { ok: boolean; text: string }[]; featured?: boolean;
}) {
  return (
    <article className={cn("relative flex flex-col rounded-2xl bg-white p-7",
      featured ? "border-2 border-brand shadow-lift" : "border border-border")} aria-label={title}>
      {featured ? (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand px-3 py-1 text-xs font-semibold text-white">{t.popularBadge}</span>
      ) : null}
      <h3 className="font-semibold text-ink">{title}</h3>
      <p className="mt-4 flex items-baseline gap-1">
        <span className="font-[var(--font-outfit)] text-4xl font-bold tabular-nums text-ink">{formatNumber(price)}</span>
        <span className="text-sm text-muted">so‘m {unit}</span>
      </p>
      <ul className="mt-6 flex-1 space-y-2.5 text-sm">
        {features.map((f) => (
          <li key={f.text} className={cn("flex gap-2", f.ok ? "text-ink" : "text-muted")}>
            <span aria-hidden="true" className={f.ok ? "font-bold text-emerald-600" : "text-slate-300"}>{f.ok ? "✓" : "–"}</span>{f.text}
          </li>
        ))}
      </ul>
      <Button asChild variant={featured ? "primary" : "outline"} className="mt-7 w-full">
        <Link href="/tariflar/">{t.choose}</Link>
      </Button>
    </article>
  );
}

export function Pricing({ tariffs, pricing }: { tariffs: Tariff[]; pricing: Pricing | null }) {
  const paid = tariffs.filter((x) => x.price_som > 0).sort((a, b) => a.price_som - b.price_som);
  if (!paid.length && !pricing) return null;
  return (
    <section className="bg-canvas" aria-labelledby="pricing">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 id="pricing" className={cn(h2, "text-center")}>{t.tariffsTitle}</h2>
        <p className="mt-2 text-center text-muted">{t.tariffsText}</p>
        <div className="mx-auto mt-10 grid max-w-5xl items-stretch gap-5 md:grid-cols-3">
          {pricing ? (
            <PriceCard title={tt.single.title} price={pricing.plan_credit_price_som} unit={tt.single.perPlan}
              features={t.singleFeatures.map((text) => ({ ok: true, text }))} />
          ) : null}
          {paid.map((x, i) => (
            <PriceCard key={x.code} title={x.name} price={x.price_som} unit={tt.perPeriod(x.duration_days)} featured={i === 0}
              features={[
                { ok: true, text: `${tt.monthly(x.monthly_limit)} (${tt.daily(x.daily_limit).toLowerCase()})` },
                { ok: true, text: t.wordExcel },
                { ok: x.ai_enabled, text: x.ai_enabled ? tt.ai : tt.noAi },
              ]} />
          ))}
        </div>
        <p className="mt-6 flex items-center justify-center gap-2 text-sm text-muted">
          {t.payWith}
          {["Click", "Payme"].map((m) => <span key={m} className="rounded-md border border-border bg-white px-2.5 py-1 font-semibold text-ink">{m}</span>)}
        </p>
      </div>
    </section>
  );
}

export function Faq() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: t.faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
  };
  return (
    <section id="savollar" className="scroll-mt-24 bg-white" aria-labelledby="faq">
      <script
        type="application/ld+json"
        // eslint-disable-next-line react/no-danger -- JSON-LD faqat shu yo'l bilan; tarkib o'zimizning matn, "<" qochirilgan
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }}
      />
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <h2 id="faq" className={cn(h2, "text-center")}>{t.faqTitle}</h2>
        <div className="mt-8 divide-y divide-border rounded-2xl border border-border">
          {t.faq.map((f, i) => (
            <details key={f.q} open={i === 0} className="group p-5">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand [&::-webkit-details-marker]:hidden">
                {f.q}
                <span aria-hidden="true" className="text-xl leading-none text-muted transition group-open:rotate-45">+</span>
              </summary>
              <p className="mt-3 text-sm leading-6 text-muted">{f.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

export function FinalCta() {
  return (
    <section className="bg-white px-4 pb-20 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-6 rounded-3xl bg-gradient-to-br from-slate-900 via-blue-900 to-brand p-8 text-white sm:p-10 md:flex-row md:items-center">
        <div>
          <h2 className="font-[var(--font-outfit)] text-2xl font-bold sm:text-3xl">{t.ctaTitle}</h2>
          <p className="mt-2 text-blue-100">{t.ctaText}</p>
        </div>
        <Button asChild size="lg" variant="outline" className="border-white/30 bg-white text-ink">
          <Link href="/dashboard/">{t.ctaAction}</Link>
        </Button>
      </div>
    </section>
  );
}

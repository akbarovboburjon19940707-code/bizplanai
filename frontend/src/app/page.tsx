import type { Metadata } from "next";
import Link from "next/link";
import { getAllProducts, getCategories, getPopularProducts, getPricing, getTariffs } from "@/features/catalog/build-data";
import { HeroArt } from "@/features/marketing/hero-art";
import { DocumentContents, Faq, FinalCta, Popular, Pricing, StatsBar, Steps } from "@/features/marketing/sections";
import { uz } from "@/messages/uz";
import { Button } from "@/shared/ui/button";

export const metadata: Metadata = { alternates: { canonical: "/" } };
const t = uz.home;

// Build vaqtida API'dan: rejalar soni, mashhur rejalar, toifalar va narxlar statik HTML'ga yoziladi (SEO, tez yuklanish)
export default async function HomePage() {
  const [all, popular, categories, tariffs, pricing] = await Promise.all([
    getAllProducts().catch(() => []), getPopularProducts(4).catch(() => []), getCategories().catch(() => []),
    getTariffs().catch(() => []), getPricing(),
  ]);
  return (
    <>
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-50 to-white">
        <div aria-hidden="true" className="hero-grid absolute inset-0 opacity-60" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 pb-16 pt-12 sm:px-6 lg:grid-cols-[1.05fr_.95fr] lg:px-8 lg:pt-20">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
              <span aria-hidden="true" className="size-1.5 rounded-full bg-emerald-500" />{t.eyebrow}
            </p>
            <h1 className="mt-5 font-[var(--font-outfit)] text-4xl font-bold leading-[1.08] tracking-tight text-ink sm:text-5xl lg:text-[3.4rem]">
              {t.titleStart}<span className="text-brand">{t.titleAccent}</span>{t.titleEnd}
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-muted">{t.description}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg" className="shadow-lg shadow-blue-600/25">
                <Link href="/dashboard/">{t.primaryAction} →</Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/katalog/">{t.secondaryAction(all.length)}</Link>
              </Button>
            </div>
            <ul className="mt-8 grid max-w-xl grid-cols-1 gap-2.5 text-sm text-ink sm:grid-cols-2">
              {t.highlights.map((x) => (
                <li key={x} className="flex gap-2"><span aria-hidden="true" className="font-bold text-emerald-600">✓</span>{x}</li>
              ))}
            </ul>
          </div>
          <HeroArt />
        </div>
      </section>
      <StatsBar plans={all.length} />
      <DocumentContents />
      <Steps />
      <Popular products={popular} categories={categories} total={all.length} />
      <Pricing tariffs={tariffs} pricing={pricing} />
      <Faq />
      <FinalCta />
    </>
  );
}

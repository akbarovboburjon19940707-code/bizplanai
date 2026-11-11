import Link from "next/link";
import { getPopularProducts, getTariffs } from "@/features/catalog/build-data";
import { HeroArt } from "@/features/marketing/hero-art";
import { Features, FinalCta, Popular, Steps, TariffStrip } from "@/features/marketing/sections";
import { uz } from "@/messages/uz";
import { Button } from "@/shared/ui/button";

// Build vaqtida API'dan: mashhur rejalar va tariflar statik HTML'ga yoziladi (SEO, tez yuklanish)
export default async function HomePage() {
  const [popular, tariffs] = await Promise.all([getPopularProducts(6), getTariffs()]);
  return (
    <>
      <section className="mx-auto grid min-h-[calc(100vh-9rem)] max-w-7xl items-center px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16 lg:px-8">
        <div className="max-w-2xl">
          <p className="mb-5 inline-flex rounded-full border border-blue-100 bg-white px-4 py-2 text-sm font-semibold text-brand shadow-sm">
            {uz.home.eyebrow}
          </p>
          <h1 className="font-[var(--font-outfit)] text-4xl font-bold leading-tight tracking-tight text-ink sm:text-5xl lg:text-6xl">
            {uz.home.title}
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-muted">{uz.home.description}</p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Button asChild size="lg">
              <Link href="/dashboard/">{uz.home.primaryAction}</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/katalog/">{uz.home.secondaryAction}</Link>
            </Button>
          </div>
          <p className="mt-4 text-sm font-medium text-muted">{uz.home.phaseLabel}</p>
        </div>
        <HeroArt />
      </section>
      <Steps />
      <Features />
      <Popular products={popular} />
      <TariffStrip tariffs={tariffs} />
      <FinalCta />
    </>
  );
}

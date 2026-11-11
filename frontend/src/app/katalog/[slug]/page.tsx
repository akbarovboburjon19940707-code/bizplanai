import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BuyBox } from "@/features/catalog/buy-box";
import { CATALOG_SKIPPED, getAllProducts, getCategories, getProductBySlug } from "@/features/catalog/build-data";
import { ProductCover } from "@/features/catalog/product-card";
import { uz } from "@/messages/uz";
import { formatNumber } from "@/shared/lib/format";

const t = uz.catalog;
type Params = { params: Promise<{ slug: string }> };

// Har mahsulot uchun build vaqtida HTML (SEO). Yangi mahsulot qo'shilsa sayt qayta deploy qilinadi.
export const dynamicParams = false;
export async function generateStaticParams() {
  if (CATALOG_SKIPPED) return [{ slug: "_" }];
  return (await getAllProducts()).map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const product = await getProductBySlug((await params).slug);
  if (!product) return { title: uz.appName, robots: { index: false } };
  const title = `${product.title} | ${uz.appName}`;
  return {
    title,
    description: product.description,
    alternates: { canonical: `/katalog/${product.slug}/` },
    openGraph: { title, description: product.description, type: "article" },
  };
}

export default async function ProductPage({ params }: Params) {
  const product = await getProductBySlug((await params).slug);
  if (!product) notFound();
  const category = (await getCategories()).find((c) => c.key === product.category_key);

  return (
    <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <Link href="/katalog/" className="text-sm font-semibold text-brand hover:underline">{t.back}</Link>
      <div className="mt-5 grid items-start gap-8 lg:grid-cols-[1fr_22rem]">
        <article className="min-w-0">
          {category ? (
            <Link href={`/katalog/?category=${category.key}`} className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-brand-dark hover:bg-blue-100">
              <span aria-hidden="true">{category.icon}</span>{category.label}
            </Link>
          ) : null}
          <h1 className="mt-3 font-[var(--font-outfit)] text-2xl font-bold leading-tight tracking-tight text-ink sm:text-3xl">{product.title}</h1>
          <ProductCover product={product} eager className="mt-6 aspect-[16/10] w-full rounded-card border border-border" />
          <p className="mt-6 whitespace-pre-line leading-7 text-ink">{product.description}</p>
          <h2 className="mt-8 text-lg font-bold text-ink">{t.includes}</h2>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {t.includesList.map((item) => (
              <li key={item} className="flex gap-2 text-sm text-ink"><span aria-hidden="true" className="font-bold text-emerald-600">✓</span>{item}</li>
            ))}
          </ul>
        </article>
        <aside className="flex flex-col gap-4 lg:sticky lg:top-24">
          <BuyBox product={product} />
          <dl className="grid grid-cols-2 gap-3 rounded-card border border-border bg-white p-5 text-sm">
            <dt className="text-muted">{t.format}</dt><dd className="text-right font-semibold">PDF</dd>
            {product.file_size ? (<><dt className="text-muted">{t.fileSize}</dt><dd className="text-right font-semibold">{product.file_size}</dd></>) : null}
            <dt className="text-muted">{t.viewsLabel}</dt><dd className="text-right font-semibold tabular-nums">{formatNumber(product.views)}</dd>
            <dt className="text-muted">{t.downloadsLabel}</dt><dd className="text-right font-semibold tabular-nums">{formatNumber(product.downloads)}</dd>
          </dl>
        </aside>
      </div>
    </section>
  );
}

import Link from "next/link";
import { uz } from "@/messages/uz";
import { formatNumber, formatSom } from "@/shared/lib/format";
import { CoverImage } from "./cover-image";
import type { Product } from "./types";

/** Muqova: API'dagi imzolangan rasm (302); rasm yo'q yoki yuklanmasa gradient. */
export function ProductCover({ product, className, eager }: { product: Product; className?: string; eager?: boolean }) {
  return <CoverImage src={product.preview_image} title={product.title} className={className} eager={eager} />;
}

export function ProductCard({ product }: { product: Product }) {
  return (
    <article className="group flex flex-col overflow-hidden rounded-card border border-border bg-white shadow-soft transition hover:-translate-y-0.5 hover:border-blue-200">
      <Link href={`/katalog/${product.slug}/`} className="flex flex-1 flex-col focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand">
        <ProductCover product={product} className="aspect-[16/10] w-full" />
        <div className="flex flex-1 flex-col p-4">
          <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-ink group-hover:text-brand">{product.title}</h3>
          <p className="mt-1.5 line-clamp-2 text-xs text-muted">{product.description}</p>
          <div className="mt-auto flex items-end justify-between gap-2 pt-4">
            <span className="text-base font-bold tabular-nums text-ink">{formatSom(product.price_som)}</span>
            <span className="text-xs text-muted">
              {formatNumber(product.downloads)} {uz.catalog.downloads}
            </span>
          </div>
        </div>
      </Link>
    </article>
  );
}

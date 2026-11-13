import { uz } from "@/messages/uz";
import { getAllProducts } from "./build-data";
import { ProductCard } from "./product-card";

const t = uz.catalog;

/**
 * Katalogning statik HTML'dagi ko'rinishi (JS ishga tushguncha va qidiruv tizimlari uchun).
 * Brauzerda CatalogBrowser uni filtr/qidiruvli jonli ro'yxat bilan almashtiradi.
 */
export async function CatalogStaticGrid() {
  const all = await getAllProducts().catch(() => []);
  const items = all.slice(0, 24);
  return (
    <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="font-[var(--font-outfit)] text-2xl font-bold tracking-tight text-ink sm:text-3xl">{t.title}</h1>
      <p className="mt-1.5 max-w-2xl text-sm text-muted">{t.subtitle}</p>
      {all.length ? <p className="mt-6 text-sm text-muted">{t.found(all.length)}</p> : null}
      <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {items.map((p) => <ProductCard key={p.id} product={p} />)}
      </div>
    </section>
  );
}

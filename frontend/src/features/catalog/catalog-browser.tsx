"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { uz } from "@/messages/uz";
import { useApi } from "@/shared/api/use-api";
import { cn } from "@/shared/lib/cn";
import { Button } from "@/shared/ui/button";
import { inputClass } from "@/shared/ui/form-field";
import { ProductCard } from "./product-card";
import type { Category, ProductPage } from "./types";
import { PAGE_SIZE, useCatalogQuery, useDebounced } from "./use-catalog-query";

const t = uz.catalog;

function CategoryTabs({ categories, active, onPick }: { categories: Category[]; active: string; onPick: (key: string) => void }) {
  const total = categories.reduce((n, c) => n + c.count, 0);
  const items = [{ key: "", label: t.all, icon: "", count: total }, ...categories];
  return (
    <div className="-mx-4 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0" role="group" aria-label={t.category}>
      <div className="flex w-max gap-2 sm:w-auto sm:flex-wrap">
        {items.map((c) => (
          <button
            key={c.key || "all"}
            type="button"
            onClick={() => onPick(c.key)}
            aria-pressed={active === c.key}
            className={cn(
              "flex items-center gap-1.5 whitespace-nowrap rounded-full border px-3.5 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand",
              active === c.key ? "border-brand bg-brand text-white" : "border-border bg-white text-ink hover:border-blue-200",
            )}
          >
            {c.icon ? <span aria-hidden="true">{c.icon}</span> : null}
            {c.label}
            <span className={cn("text-xs", active === c.key ? "text-blue-100" : "text-muted")}>{c.count}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function Pagination({ page, pages, onPage }: { page: number; pages: number; onPage: (p: number) => void }) {
  if (pages <= 1) return null;
  return (
    <nav aria-label={t.pagination} className="mt-8 flex items-center justify-center gap-3">
      <Button variant="outline" disabled={page <= 1} onClick={() => onPage(page - 1)}>{t.prev}</Button>
      <span className="text-sm tabular-nums text-muted" aria-current="page">{t.page(page, pages)}</span>
      <Button variant="outline" disabled={page >= pages} onClick={() => onPage(page + 1)}>{t.next}</Button>
    </nav>
  );
}

export function CatalogBrowser() {
  const { category, q, page, update } = useCatalogQuery();
  const [search, setSearch] = useState(q);
  const debounced = useDebounced(search, 400);
  const categories = useApi<Category[]>("/v1/catalog/categories");

  useEffect(() => setSearch(q), [q]); // orqaga/oldinga tugmalari
  useEffect(() => {
    if (debounced.trim() !== q) update({ q: debounced });
  }, [debounced]); // eslint-disable-line react-hooks/exhaustive-deps -- faqat yozish to'xtaganda

  const sp = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String((page - 1) * PAGE_SIZE) });
  if (category) sp.set("category", category);
  if (q) sp.set("q", q);
  const products = useApi<ProductPage>(`/v1/catalog/products?${sp.toString()}`);
  const data = products.data;
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="font-[var(--font-outfit)] text-2xl font-bold tracking-tight text-ink sm:text-3xl">{t.title}</h1>
      <p className="mt-1.5 max-w-2xl text-sm text-muted">{t.subtitle}</p>

      <div className="mt-6 flex flex-col gap-4">
        <div className="relative max-w-xl">
          <label htmlFor="catalog-q" className="sr-only">{t.search}</label>
          <input
            id="catalog-q"
            type="search"
            value={search}
            maxLength={100}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t.searchPlaceholder}
            className={cn(inputClass, "py-3 pl-10")}
          />
          <svg viewBox="0 0 20 20" aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-slate-400">
            <circle cx="9" cy="9" r="6" fill="none" stroke="currentColor" strokeWidth="2" />
            <path d="M14 14l4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        {categories.data ? <CategoryTabs categories={categories.data} active={category} onPick={(key) => update({ category: key })} /> : <div className="h-10 animate-pulse rounded-full bg-white" />}
      </div>

      <p className="mt-6 text-sm text-muted" aria-live="polite">{data ? t.found(data.total) : " "}</p>

      {products.error ? (
        <p className="mt-6 text-sm text-red-600">
          {products.error.message || t.loadError}{" "}
          <button type="button" onClick={products.reload} className="font-semibold text-brand hover:underline">{t.retry}</button>
        </p>
      ) : !data ? (
        <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" aria-busy="true">
          {Array.from({ length: 8 }, (_, i) => <div key={i} className="h-72 animate-pulse rounded-card bg-white" />)}
        </div>
      ) : data.items.length === 0 ? (
        <div className="mt-10 text-center">
          <p className="text-muted">{t.empty}</p>
          {category || q ? (
            <Button variant="outline" className="mt-4" onClick={() => { setSearch(""); update({ category: "", q: "" }); }}>{t.clear}</Button>
          ) : null}
        </div>
      ) : (
        <div className={cn("mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4", products.loading && "opacity-60")}>
          {data.items.map((p) => <ProductCard key={p.id} product={p} />)}
        </div>
      )}
      <Pagination page={page} pages={pages} onPage={(p) => update({ page: p })} />

      <div className="mt-12 flex flex-col items-start gap-3 rounded-card bg-gradient-to-br from-slate-900 via-blue-900 to-blue-600 p-6 text-white sm:flex-row sm:items-center sm:justify-between">
        <p className="text-lg font-semibold">{t.customCta}</p>
        <Button asChild variant="outline" className="border-white/30 bg-white text-ink"><Link href="/dashboard/">{t.customCtaButton}</Link></Button>
      </div>
    </section>
  );
}

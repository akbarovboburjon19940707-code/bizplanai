"use client";

import { useEffect, useState } from "react";
import type { Category } from "@/features/catalog/types";
import { uz } from "@/messages/uz";
import { useApi } from "@/shared/api/use-api";
import { cn } from "@/shared/lib/cn";
import { Button } from "@/shared/ui/button";
import { inputClass } from "@/shared/ui/form-field";
import { LoadError } from "./admin-shell";
import { ProductRow } from "./product-row";
import type { AdminProduct, AdminProductPage } from "./types";
import { useDebouncedSearch } from "./use-debounced-search";

const t = uz.admin.catalog;
type Filter = keyof typeof t.filters;
const ACTIVE: Record<Filter, string | null> = { all: null, active: "true", hidden: "false" };
const PAGE = 30;

export function CatalogAdminView() {
  const search = useDebouncedSearch();
  const [filter, setFilter] = useState<Filter>("all");
  const [page, setPage] = useState(0);
  const [items, setItems] = useState<AdminProduct[] | null>(null);
  const categories = useApi<Category[]>("/v1/catalog/categories");

  useEffect(() => setPage(0), [search.query, filter]);
  const qs = new URLSearchParams({ limit: String(PAGE), offset: String(page * PAGE) });
  if (search.query) qs.set("q", search.query);
  if (ACTIVE[filter]) qs.set("active", ACTIVE[filter]!);
  const list = useApi<AdminProductPage>(`/v1/admin/catalog/products?${qs.toString()}`);
  useEffect(() => setItems(list.data?.items ?? null), [list.data]);

  const labels = new Map((categories.data ?? []).map((c) => [c.key, c.label]));
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / PAGE)) : 1;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <label htmlFor="admin-catalog-q" className="sr-only">{uz.admin.search}</label>
        <input id="admin-catalog-q" type="search" maxLength={100} value={search.input} placeholder={t.placeholder}
          onChange={(e) => search.setInput(e.target.value)} className={cn(inputClass, "sm:max-w-sm")} />
        <div className="flex gap-2" role="group" aria-label={uz.admin.nav.catalog}>
          {(Object.keys(t.filters) as Filter[]).map((f) => (
            <button key={f} type="button" aria-pressed={filter === f} onClick={() => setFilter(f)}
              className={cn("rounded-full border px-3.5 py-1.5 text-sm font-semibold",
                filter === f ? "border-brand bg-brand text-white" : "border-border bg-white text-ink hover:border-blue-200")}>
              {t.filters[f]}
            </button>
          ))}
        </div>
        {list.data ? <span className="text-sm text-muted sm:ml-auto">{t.total(list.data.total)}</span> : null}
      </div>
      <p className="text-xs text-muted">{t.redeployHint}</p>
      {list.error ? (
        <LoadError message={list.error.message} onRetry={list.reload} />
      ) : !items ? (
        <div className="h-64 animate-pulse rounded-card bg-white" aria-busy="true" />
      ) : items.length === 0 ? (
        <p className="text-sm text-muted">{uz.admin.empty}</p>
      ) : (
        <ul className="divide-y divide-border overflow-hidden rounded-card border border-border bg-white shadow-soft">
          {items.map((p) => (
            <ProductRow
              key={p.id}
              product={p}
              categoryLabel={labels.get(p.category_key) ?? p.category_key}
              onChange={(u) => setItems((cur) => cur?.map((x) => (x.id === u.id ? u : x)) ?? cur)}
            />
          ))}
        </ul>
      )}
      {pages > 1 ? (
        <nav aria-label={uz.catalog.pagination} className="flex items-center justify-center gap-3">
          <Button variant="outline" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>{uz.catalog.prev}</Button>
          <span className="text-sm tabular-nums text-muted">{uz.catalog.page(page + 1, pages)}</span>
          <Button variant="outline" disabled={page + 1 >= pages} onClick={() => setPage((p) => p + 1)}>{uz.catalog.next}</Button>
        </nav>
      ) : null}
    </div>
  );
}

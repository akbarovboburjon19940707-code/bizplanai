"use client";

import { useState } from "react";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { cn } from "@/shared/lib/cn";
import { formatNumber, parseNumber } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import { inputClass } from "@/shared/ui/form-field";
import type { AdminProduct } from "./types";

const t = uz.admin.catalog;
const MAX_PRICE = 100_000_000; // backend chegarasi (ProductPatch.price_som)

/** Bitta mahsulot: narxni tahrirlash va yashirish/ko'rsatish (PATCH /v1/admin/catalog/products/{id}). */
export function ProductRow({ product, categoryLabel, onChange }: {
  product: AdminProduct;
  categoryLabel: string;
  onChange: (p: AdminProduct) => void;
}) {
  const [price, setPrice] = useState(formatNumber(product.price_som));
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const parsed = parseNumber(price);
  const priceValid = parsed !== undefined && Number.isInteger(parsed) && parsed > 0 && parsed <= MAX_PRICE;
  const dirty = priceValid && parsed !== product.price_som;

  const patch = async (body: Record<string, unknown>) => {
    setBusy(true);
    setStatus(null);
    try {
      const updated = await apiRequest<AdminProduct>(`/v1/admin/catalog/products/${encodeURIComponent(product.id)}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      onChange(updated);
      setPrice(formatNumber(updated.price_som));
      setStatus({ ok: true, text: t.saved });
    } catch (e) {
      setStatus({ ok: false, text: e instanceof ApiError && e.message ? e.message : uz.authForms.genericError });
    } finally {
      setBusy(false);
    }
  };

  const inputId = `price-${product.id}`;
  return (
    <li className={cn("flex flex-col gap-3 p-4 md:flex-row md:items-center", !product.is_active && "bg-slate-50")}>
      <div className="min-w-0 flex-1">
        <p className="flex items-center gap-2 font-semibold text-ink">
          <span className="truncate">{product.title}</span>
          {!product.is_active ? <span className="shrink-0 rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700">{t.hiddenBadge}</span> : null}
        </p>
        <p className="truncate text-xs text-muted">{categoryLabel} · <span className="font-mono">{product.id}</span></p>
        {status ? <p className={cn("mt-1 text-xs font-medium", status.ok ? "text-emerald-700" : "text-red-600")} role="status">{status.text}</p> : null}
      </div>
      <form
        className="flex flex-wrap items-center gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (dirty) void patch({ price_som: parsed });
        }}
      >
        <label htmlFor={inputId} className="sr-only">{t.price}</label>
        <input
          id={inputId}
          inputMode="numeric"
          value={price}
          onChange={(e) => setPrice(formatNumber(parseNumber(e.target.value)))}
          aria-invalid={!priceValid || undefined}
          className={cn(inputClass, "w-32 text-right tabular-nums")}
        />
        <Button type="submit" size="sm" disabled={!dirty || busy}>{t.save}</Button>
        <Button type="button" size="sm" variant="outline" disabled={busy} onClick={() => void patch({ is_active: !product.is_active })}>
          {product.is_active ? t.hide : t.show}
        </Button>
        {product.is_active ? (
          <a href={`/katalog/${product.slug}/`} target="_blank" rel="noopener noreferrer" className="text-xs font-semibold text-brand hover:underline">{t.open}</a>
        ) : null}
      </form>
    </li>
  );
}

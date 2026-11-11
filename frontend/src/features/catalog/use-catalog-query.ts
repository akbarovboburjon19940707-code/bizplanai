"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

export const PAGE_SIZE = 24;

/** Katalog filtri URL'da: ?category=&q=&page= (havolani ulashsa, xuddi shu natija ochiladi). */
export function useCatalogQuery() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const category = params.get("category") ?? "";
  const q = params.get("q") ?? "";
  const page = Math.max(1, Number.parseInt(params.get("page") ?? "1", 10) || 1);

  const update = useCallback(
    (next: { category?: string; q?: string; page?: number }) => {
      const sp = new URLSearchParams();
      const c = next.category ?? category;
      const s = (next.q ?? q).trim();
      const p = next.page ?? 1; // filtr o'zgarsa birinchi sahifaga
      if (c) sp.set("category", c);
      if (s) sp.set("q", s);
      if (p > 1) sp.set("page", String(p));
      const qs = sp.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: next.page !== undefined });
    },
    [category, q, router, pathname],
  );

  return { category, q, page, update };
}

/** Qidiruv maydoni uchun kechikish (har harfda so'rov yubormaslik). */
export function useDebounced<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), ms);
    return () => window.clearTimeout(timer);
  }, [value, ms]);
  return debounced;
}

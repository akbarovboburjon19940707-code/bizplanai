import "server-only";
import type { Category, Product, ProductPage } from "./types";

/**
 * Build vaqtida katalogni API'dan oladi (static export: har mahsulot uchun alohida HTML).
 * API javob bermasa build xato bilan to'xtaydi: bo'sh yoki eskirgan katalog chiqmasin.
 * `CATALOG_STATIC=skip` faqat CI uchun (API yo'q): bitta zaxira sahifa yasaladi.
 */
const API = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
export const CATALOG_SKIPPED = process.env.CATALOG_STATIC === "skip";
const PAGE = 100;

async function getJson<T>(path: string): Promise<T> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const res = await fetch(`${API}${path}`, { headers: { Accept: "application/json" }, cache: "force-cache" });
      if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
      return (await res.json()) as T;
    } catch (error) {
      lastError = error;
      await new Promise((r) => setTimeout(r, attempt * 1000));
    }
  }
  throw new Error(`Katalogni API'dan olib bo'lmadi (${API}). ${String(lastError)}`);
}

let productsPromise: Promise<Product[]> | null = null;

export function getAllProducts(): Promise<Product[]> {
  if (CATALOG_SKIPPED) return Promise.resolve([]);
  productsPromise ??= (async () => {
    const all: Product[] = [];
    for (let offset = 0; ; offset += PAGE) {
      const page = await getJson<ProductPage>(`/v1/catalog/products?limit=${PAGE}&offset=${offset}`);
      all.push(...page.items);
      if (all.length >= page.total || page.items.length === 0) break;
    }
    if (all.length === 0) throw new Error("Katalog bo'sh: API to'g'ri bazaga ulanganini tekshiring");
    return all;
  })();
  return productsPromise;
}

export async function getProductBySlug(slug: string): Promise<Product | undefined> {
  return (await getAllProducts()).find((p) => p.slug === slug);
}

export function getCategories(): Promise<Category[]> {
  return CATALOG_SKIPPED ? Promise.resolve([]) : getJson<Category[]>("/v1/catalog/categories");
}

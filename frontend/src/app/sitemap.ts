import type { MetadataRoute } from "next";
import { getAllProducts } from "@/features/catalog/build-data";
import { SITE_URL } from "@/shared/lib/site";

export const dynamic = "force-static"; // static export: build vaqtida sitemap.xml yoziladi

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // /dashboard/ kirish talab qiladigan ish sahifasi: indeksga kerak emas
  const pages = ["/", "/katalog/", "/tariflar/", "/aloqa/"].map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: "weekly" as const,
    priority: path === "/" ? 1 : 0.8,
  }));
  const products = (await getAllProducts()).map((p) => ({
    url: `${SITE_URL}/katalog/${p.slug}/`,
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));
  return [...pages, ...products];
}

import type { Metadata } from "next";
import { Suspense } from "react";
import { CatalogBrowser } from "@/features/catalog/catalog-browser";
import { CatalogStaticGrid } from "@/features/catalog/catalog-static-grid";
import { uz } from "@/messages/uz";

export const metadata: Metadata = {
  alternates: { canonical: "/katalog/" },
  title: `${uz.catalog.title} | ${uz.appName}`,
  description: uz.catalog.subtitle,
  openGraph: { title: uz.catalog.title, description: uz.catalog.subtitle, type: "website" },
};

export default function Page() {
  return (
    <Suspense fallback={<CatalogStaticGrid />}>
      <CatalogBrowser />
    </Suspense>
  );
}

import type { Metadata } from "next";
import { TariffsPage } from "@/features/billing/tariffs-page";
import { getPricing, getTariffs } from "@/features/catalog/build-data";
import { uz } from "@/messages/uz";

export const metadata: Metadata = {
  alternates: { canonical: "/tariflar/" },
  title: `${uz.tariffs.title} | ${uz.appName}`,
  description: uz.tariffs.subtitle,
};

export default async function Page() {
  // Narxlar statik HTML'da bo'lsin (qidiruv tizimlari JS'siz ham ko'radi); brauzerda API'dan yangilanadi
  const [tariffs, pricing] = await Promise.all([getTariffs().catch(() => []), getPricing()]);
  return <TariffsPage initialTariffs={tariffs.length ? tariffs : null} initialPricing={pricing} />;
}

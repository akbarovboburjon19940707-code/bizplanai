import type { Metadata } from "next";
import { TariffsPage } from "@/features/billing/tariffs-page";
import { uz } from "@/messages/uz";

export const metadata: Metadata = {
  alternates: { canonical: "/tariflar/" },
  title: `${uz.tariffs.title} | ${uz.appName}`,
  description: uz.tariffs.subtitle,
};

export default function Page() {
  return <TariffsPage />;
}

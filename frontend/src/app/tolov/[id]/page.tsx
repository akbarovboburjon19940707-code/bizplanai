import type { Metadata } from "next";
import { PaymentStatusPage } from "@/features/payments/payment-status-page";
import { uz } from "@/messages/uz";

// Static export: bitta `_` nusxa yaratiladi, Render `/tolov/*` ni shu sahifaga yo'naltiradi (rewrite).
// Haqiqiy to'lov id si brauzerda manzildan o'qiladi.
export const dynamicParams = false;
export function generateStaticParams() {
  return [{ id: "_" }];
}

export const metadata: Metadata = { title: `${uz.payments.status.title} | ${uz.appName}`, robots: { index: false } };

export default function Page() {
  return <PaymentStatusPage />;
}

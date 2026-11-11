import type { Metadata } from "next";
import { ContactPage } from "@/features/contact/contact-page";
import { uz } from "@/messages/uz";

export const metadata: Metadata = {
  alternates: { canonical: "/aloqa/" },
  title: `${uz.contact.title} | ${uz.appName}`,
  description: uz.contact.subtitle,
};

export default function Page() {
  return <ContactPage />;
}

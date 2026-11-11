"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { uz } from "@/messages/uz";
import { CONTACTS } from "@/shared/config/contacts";

const t = uz.contact.footer;
const nav = uz.navigation;
const linkClass = "text-sm text-muted transition hover:text-brand focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand rounded";

export function SiteFooter() {
  // Telegram Mini App'da footer kerak emas (sarlavha kabi)
  if (usePathname()?.startsWith("/tg")) return null;
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:grid-cols-2 sm:px-6 lg:grid-cols-[2fr_1fr_1fr] lg:px-8">
        <div className="max-w-sm">
          <p className="text-lg font-bold text-ink">{uz.appName}</p>
          <p className="mt-2 text-sm text-muted">{t.about}</p>
          <ul className="mt-4 flex flex-wrap gap-x-4 gap-y-2">
            {CONTACTS.socials.map((s) => (
              <li key={s.href}>
                <a href={s.href} target="_blank" rel="noopener noreferrer" className={linkClass}>{s.name}</a>
              </li>
            ))}
          </ul>
        </div>
        <nav aria-label={t.platform}>
          <p className="text-sm font-semibold text-ink">{t.platform}</p>
          <ul className="mt-3 flex flex-col gap-2">
            <li><Link href="/dashboard/" className={linkClass}>{nav.createPlan}</Link></li>
            <li><Link href="/katalog/" className={linkClass}>{nav.catalog}</Link></li>
            <li><Link href="/tariflar/" className={linkClass}>{nav.tariffs}</Link></li>
            <li><Link href="/aloqa/" className={linkClass}>{nav.contact}</Link></li>
          </ul>
        </nav>
        <div>
          <p className="text-sm font-semibold text-ink">{t.contact}</p>
          <ul className="mt-3 flex flex-col gap-2">
            <li><a href={CONTACTS.phone.href} className={linkClass}>{CONTACTS.phone.display}</a></li>
            <li><a href={CONTACTS.telegram.href} target="_blank" rel="noopener noreferrer" className={linkClass}>Telegram: {CONTACTS.telegram.display}</a></li>
            <li><a href={CONTACTS.email.href} className={linkClass}>{CONTACTS.email.display}</a></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-100">
        <p className="mx-auto max-w-7xl px-4 py-4 text-xs text-muted sm:px-6 lg:px-8">{t.rights(new Date().getFullYear())}</p>
      </div>
    </footer>
  );
}

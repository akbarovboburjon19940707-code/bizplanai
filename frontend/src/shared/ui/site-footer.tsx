"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { uz } from "@/messages/uz";
import { CONTACTS } from "@/shared/config/contacts";
import { cn } from "@/shared/lib/cn";
import { SITE_URL } from "@/shared/lib/site";
import { BrandLogo } from "./brand-logo";
import { ClockIcon, FacebookIcon, MailIcon, PhoneIcon, SOCIAL_ICONS, ShareIcon, TelegramIcon } from "./icons";

const t = uz.contact.footer;
const nav = uz.navigation;
const focus = "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900";
const linkClass = cn("rounded text-sm text-slate-300 transition hover:text-white", focus);
const headingClass = "text-sm font-semibold uppercase tracking-wider text-white";
const socialHover = { telegram: "hover:bg-[#229ED9]", instagram: "hover:bg-pink-600", youtube: "hover:bg-red-600" } as const;

/** Joriy sahifa havolasini ulashish: telefonda tizim oynasi (Web Share), bo'lmasa havolani nusxalash. */
function ShareStrip({ url }: { url: string }) {
  const [copied, setCopied] = useState(false);
  const encoded = encodeURIComponent(url);
  const text = encodeURIComponent(t.shareMessage);
  const btn = cn("inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition", focus);

  async function share() {
    try {
      if (navigator.share) {
        await navigator.share({ title: uz.appName, text: t.shareMessage, url });
        return;
      }
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      /* foydalanuvchi bekor qildi yoki clipboard ruxsati yo'q */
    }
  }

  return (
    <div className="border-b border-white/10">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-4 px-4 py-6 sm:px-6 md:flex-row md:items-center lg:px-8">
        <div>
          <p className="font-semibold text-white">{t.shareTitle}</p>
          <p className="mt-0.5 text-sm text-slate-400">{t.shareText}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button type="button" onClick={share} className={cn(btn, "border border-white/15 bg-white/5 hover:bg-white/10")}>
            <ShareIcon className="size-4" />
            <span aria-live="polite">{copied ? t.shareCopied : t.share}</span>
          </button>
          <a href={`https://www.facebook.com/sharer/sharer.php?u=${encoded}`} target="_blank" rel="noopener noreferrer"
            className={cn(btn, "bg-[#1877F2] hover:bg-[#166FE5]")}>
            <FacebookIcon className="size-4" />Facebook
          </a>
          <a href={`https://t.me/share/url?url=${encoded}&text=${text}`} target="_blank" rel="noopener noreferrer"
            className={cn(btn, "bg-[#229ED9] hover:bg-[#1E8EC4]")}>
            <TelegramIcon className="size-4" />Telegram
          </a>
        </div>
      </div>
    </div>
  );
}

function ContactRow({ icon, tone, children }: { icon: React.ReactNode; tone: string; children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-3">
      <span className={cn("grid size-8 shrink-0 place-items-center rounded-lg bg-white/10", tone)}>{icon}</span>
      {children}
    </li>
  );
}

export function SiteFooter() {
  const pathname = usePathname();
  // Telegram Mini App'da footer kerak emas (sarlavha kabi)
  if (pathname?.startsWith("/tg")) return null;
  // Shaxsiy sahifalar (kabinet, to'lov) emas, saytning ommaviy sahifasi ulashiladi
  const privatePage = /^\/(kabinet|tolov|admin|reja|kirish|royxat)\//.test(pathname ?? "");
  const shareUrl = `${SITE_URL}${privatePage ? "/" : pathname ?? "/"}`;

  return (
    <footer className="bg-gradient-to-b from-[#0b1730] to-slate-900 text-slate-300">
      <ShareStrip url={shareUrl} />
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:grid-cols-2 sm:px-6 lg:grid-cols-[1.6fr_1fr_1.3fr] lg:px-8">
        <div className="max-w-sm">
          <Link href="/" className={cn("inline-flex items-center gap-2.5 rounded-lg", focus)}>
            <BrandLogo size={36} />
            <span className="font-[var(--font-outfit)] text-xl font-bold text-white">{uz.appName}</span>
          </Link>
          <p className="mt-4 text-sm leading-6 text-slate-400">{t.about}</p>
          <ul className="mt-5 flex gap-2.5">
            {CONTACTS.socials.map((s) => {
              const Icon = SOCIAL_ICONS[s.icon];
              return (
                <li key={s.href}>
                  <a href={s.href} target="_blank" rel="noopener noreferrer" aria-label={s.name} title={s.name}
                    className={cn("grid size-10 place-items-center rounded-full bg-white/10 text-white transition", socialHover[s.icon], focus)}>
                    <Icon className="size-5" />
                  </a>
                </li>
              );
            })}
          </ul>
        </div>
        <nav aria-label={t.platform}>
          <p className={headingClass}>{t.platform}</p>
          <ul className="mt-4 flex flex-col gap-2.5">
            <li><Link href="/dashboard/" className={linkClass}>{nav.createPlan}</Link></li>
            <li><Link href="/katalog/" className={linkClass}>{nav.catalog}</Link></li>
            <li><Link href="/tariflar/" className={linkClass}>{nav.tariffs}</Link></li>
            <li><Link href="/aloqa/" className={linkClass}>{nav.contact}</Link></li>
          </ul>
        </nav>
        <div>
          <p className={headingClass}>{t.contact}</p>
          <ul className="mt-4 flex flex-col gap-3 text-sm">
            <ContactRow icon={<PhoneIcon className="size-4" />} tone="text-blue-300">
              <a href={CONTACTS.phone.href} className={cn(linkClass, "font-semibold text-white")}>{CONTACTS.phone.display}</a>
            </ContactRow>
            <ContactRow icon={<TelegramIcon className="size-4" />} tone="text-sky-300">
              <a href={CONTACTS.telegram.href} target="_blank" rel="noopener noreferrer" className={linkClass}>{CONTACTS.telegram.display}</a>
            </ContactRow>
            <ContactRow icon={<MailIcon className="size-4" />} tone="text-blue-300">
              <a href={CONTACTS.email.href} className={linkClass}>{CONTACTS.email.display}</a>
            </ContactRow>
            <ContactRow icon={<ClockIcon className="size-4" />} tone="text-emerald-300">
              <span>{CONTACTS.hours}</span>
            </ContactRow>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10">
        {/* Pastki o'ngda "Savol berish" tugmasi turadi: matn chapda, mobilda pastdan joy qoldiriladi */}
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 pb-24 pt-5 text-xs text-slate-400 sm:px-6 md:flex-row md:items-center md:gap-8 md:pb-5 lg:px-8">
          <p>{t.rights(new Date().getFullYear())}</p>
          <p className="flex items-center gap-2">
            {t.payments}
            <span className="rounded bg-white/10 px-2 py-0.5 font-semibold text-slate-200">Click</span>
            <span className="rounded bg-white/10 px-2 py-0.5 font-semibold text-slate-200">Payme</span>
          </p>
        </div>
      </div>
    </footer>
  );
}

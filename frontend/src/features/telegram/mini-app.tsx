"use client";

import Link from "next/link";
import Script from "next/script";
import { RecentPlans } from "@/features/account/history-lists";
import { SubscriptionCard } from "@/features/account/subscription-card";
import { useAuth } from "@/features/auth/auth-context";
import { uz } from "@/messages/uz";
import { useApi } from "@/shared/api/use-api";
import type { components } from "@/shared/api/schema";
import { Button } from "@/shared/ui/button";
import { useTelegramSession } from "./use-telegram-session";

type MeOut = components["schemas"]["MeOut"];
const t = uz.telegram;

// Telegram mavzusi: SDK --tg-theme-* o'zgaruvchilarini qo'yadi, bo'lmasa sayt ranglari
const theme = {
  background: "var(--tg-theme-secondary-bg-color, #f0f2f5)",
  color: "var(--tg-theme-text-color, #0f172a)",
} as const;

function Tile({ href, title, hint, primary }: { href: string; title: string; hint?: string; primary?: boolean }) {
  return (
    <Link
      href={href}
      className={
        primary
          ? "col-span-2 flex flex-col rounded-card bg-brand p-4 text-white shadow-soft active:scale-[0.99]"
          : "flex items-center justify-center rounded-card border border-border bg-white p-4 text-center text-sm font-semibold text-ink shadow-soft active:scale-[0.99]"
      }
      style={primary ? { background: "var(--tg-theme-button-color, #2563eb)", color: "var(--tg-theme-button-text-color, #fff)" } : undefined}
    >
      <span className={primary ? "text-lg font-bold" : ""}>{title}</span>
      {hint ? <span className="mt-0.5 text-sm opacity-80">{hint}</span> : null}
    </Link>
  );
}

function Dashboard() {
  const { user } = useAuth();
  const me = useApi<MeOut>("/v1/me");
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="font-[var(--font-outfit)] text-2xl font-bold">{t.hello(user?.first_name ?? "")}</h1>
        <p className="text-sm opacity-70">{t.subtitle}</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Tile href="/dashboard/" title={t.actions.create} hint={t.actions.createHint} primary />
        <Tile href="/katalog/" title={t.actions.catalog} />
        <Tile href="/tariflar/" title={t.actions.tariffs} />
      </div>
      {me.data ? <SubscriptionCard subscription={me.data.subscription} credits={me.data.user.plan_credits} /> : <div className="h-40 animate-pulse rounded-card bg-white" />}
      <RecentPlans />
      <Button asChild variant="outline"><Link href="/kabinet/">{t.actions.account}</Link></Button>
    </div>
  );
}

function Message({ title, text, action }: { title: string; text: string; action?: boolean }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center">
      <h1 className="text-xl font-bold">{title}</h1>
      <p className="max-w-xs text-sm opacity-70">{text}</p>
      {action ? <Button asChild className="mt-2"><Link href="/kirish/">{t.toSite}</Link></Button> : null}
    </div>
  );
}

/** /tg: Telegram Mini App. SDK faqat shu sahifada yuklanadi (CSP: script-src https://telegram.org). */
export function MiniApp() {
  const { state, init } = useTelegramSession();
  return (
    <section className="min-h-screen px-4 py-5" style={theme}>
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" onReady={() => void init()} onError={() => void init()} />
      <div className="mx-auto max-w-md">
        {state.phase === "loading" ? (
          <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3" aria-busy="true">
            <span className="size-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
            <p className="text-sm opacity-70">{t.loading}</p>
          </div>
        ) : state.phase === "outside" ? (
          <Message title={t.outsideTitle} text={t.outsideText} action />
        ) : state.phase === "error" ? (
          <Message title={t.errorTitle} text={state.message || t.errorText} />
        ) : (
          <Dashboard />
        )}
      </div>
    </section>
  );
}

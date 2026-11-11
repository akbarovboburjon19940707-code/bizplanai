"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useAuth } from "@/features/auth/auth-context";
import { RequireAuth } from "@/features/auth/require-auth";
import { uz } from "@/messages/uz";
import { cn } from "@/shared/lib/cn";

const t = uz.admin;
const TABS = [
  { href: "/admin/", label: t.nav.stats },
  { href: "/admin/tolovlar/", label: t.nav.payments },
  { href: "/admin/foydalanuvchilar/", label: t.nav.users },
  { href: "/admin/katalog/", label: t.nav.catalog },
  { href: "/admin/murojaatlar/", label: t.nav.messages },
] as const;

function NotFoundView() {
  // Admin bo'lmaganga panel borligini oshkor qilmaymiz: oddiy 404 ko'rinishi
  return (
    <section className="mx-auto flex min-h-[60vh] max-w-3xl flex-col items-center justify-center px-6 py-16 text-center">
      <p className="text-sm font-bold uppercase tracking-[0.2em] text-brand">404</p>
      <h1 className="mt-4 text-3xl font-bold tracking-tight text-ink">{t.notFoundTitle}</h1>
      <Link className="mt-7 rounded-control bg-brand px-5 py-3 font-semibold text-white hover:bg-brand-hover" href="/">
        {uz.navigation.home}
      </Link>
    </section>
  );
}

function Skeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-4 px-4 py-8 sm:px-6 lg:px-8" aria-busy="true">
      <div className="h-8 w-48 animate-pulse rounded bg-slate-200" />
      <div className="h-40 animate-pulse rounded-card bg-white" />
    </div>
  );
}

function AdminOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const pathname = usePathname();
  if (user?.role !== "admin") return <NotFoundView />;
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <h1 className="font-[var(--font-outfit)] text-2xl font-bold text-ink">{t.title}</h1>
      <nav aria-label={t.title} className="-mx-4 mt-4 overflow-x-auto border-b border-border px-4 sm:mx-0 sm:px-0">
        <div className="flex w-max gap-1">
          {TABS.map((tab) => {
            const active = tab.href === "/admin/" ? pathname === "/admin/" || pathname === "/admin" : pathname?.startsWith(tab.href.slice(0, -1));
            return (
              <Link
                key={tab.href}
                href={tab.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "-mb-px border-b-2 px-4 py-2.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand",
                  active ? "border-brand text-brand" : "border-transparent text-muted hover:text-ink",
                )}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>
      </nav>
      <div className="mt-6">{children}</div>
    </div>
  );
}

export function AdminShell({ children }: { children: ReactNode }) {
  return (
    <RequireAuth fallback={<Skeleton />}>
      <AdminOnly>{children}</AdminOnly>
    </RequireAuth>
  );
}

export function LoadError({ message, onRetry }: { message?: string; onRetry: () => void }) {
  return (
    <p className="text-sm text-red-600">
      {message || t.loadError}{" "}
      <button type="button" onClick={onRetry} className="font-semibold text-brand hover:underline">{t.retry}</button>
    </p>
  );
}

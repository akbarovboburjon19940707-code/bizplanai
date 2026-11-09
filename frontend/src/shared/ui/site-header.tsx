"use client";

import Link from "next/link";
import { useAuth } from "@/features/auth/auth-context";
import { uz } from "@/messages/uz";

export function SiteHeader() {
  const { status, user, signOut } = useAuth();

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3" aria-label={uz.appName}>
          <span className="grid size-10 place-items-center rounded-xl bg-brand text-lg font-bold text-white">B</span>
          <span className="text-lg font-bold tracking-tight text-ink">{uz.appName}</span>
        </Link>
        <div className="flex items-center gap-3">
          <span
            aria-live="polite"
            className={`hidden rounded-full px-3 py-1.5 text-xs font-semibold sm:inline-flex ${
              status === "loading"
                ? "bg-slate-100 text-slate-500"
                : status === "authenticated"
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-slate-100 text-slate-600"
            }`}
          >
            {status === "loading"
              ? uz.auth.loading
              : status === "authenticated"
                ? user?.first_name || uz.auth.signedIn
                : uz.auth.guest}
          </span>
          {status === "authenticated" ? (
            <button
              type="button"
              onClick={() => void signOut()}
              className="rounded-control border border-border px-4 py-2 text-sm font-semibold text-ink transition hover:bg-canvas focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
            >
              {uz.navigation.signOut}
            </button>
          ) : null}
        </div>
      </div>
    </header>
  );
}

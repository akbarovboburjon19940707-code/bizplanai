import type { ReactNode } from "react";

/** Kirish va ro'yxat sahifalari uchun umumiy karta. */
export function AuthCard({ title, subtitle, children, footer }: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <section className="mx-auto flex w-full max-w-md flex-col px-4 py-10 sm:py-16">
      <div className="rounded-card border border-border bg-white p-6 shadow-soft sm:p-8">
        <h1 className="font-[var(--font-outfit)] text-2xl font-bold tracking-tight text-ink">{title}</h1>
        <p className="mt-1.5 text-sm text-muted">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </div>
      <p className="mt-5 text-center text-sm text-muted">{footer}</p>
    </section>
  );
}

export function AuthSkeleton() {
  return (
    <section className="mx-auto w-full max-w-md px-4 py-10 sm:py-16" aria-busy="true">
      <div className="space-y-4 rounded-card border border-border bg-white p-6 shadow-soft sm:p-8">
        <div className="h-7 w-32 animate-pulse rounded bg-slate-200" />
        <div className="h-4 w-56 animate-pulse rounded bg-slate-100" />
        <div className="h-11 animate-pulse rounded-control bg-slate-100" />
        <div className="h-11 animate-pulse rounded-control bg-slate-100" />
        <div className="h-11 animate-pulse rounded-control bg-slate-200" />
      </div>
    </section>
  );
}

export function OrDivider({ label }: { label: string }) {
  return (
    <div className="my-5 flex items-center gap-3 text-xs font-medium uppercase tracking-wide text-slate-400" aria-hidden="true">
      <span className="h-px flex-1 bg-border" />
      {label}
      <span className="h-px flex-1 bg-border" />
    </div>
  );
}

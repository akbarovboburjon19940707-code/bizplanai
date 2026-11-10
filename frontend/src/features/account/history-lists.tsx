"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { uz } from "@/messages/uz";
import { useApi } from "@/shared/api/use-api";
import type { components } from "@/shared/api/schema";
import { cn } from "@/shared/lib/cn";
import { formatDate, formatSom } from "@/shared/lib/format";

type PlanOut = components["schemas"]["PlanOut"];
type PaymentOut = components["schemas"]["PaymentOut"];
const t = uz.account;

const TONE: Record<string, string> = {
  done: "bg-emerald-50 text-emerald-700",
  paid: "bg-emerald-50 text-emerald-700",
  failed: "bg-red-50 text-red-700",
  rejected: "bg-red-50 text-red-700",
  cancelled: "bg-slate-100 text-slate-600",
};

function Badge({ status, label }: { status: string; label: string }) {
  return (
    <span className={cn("shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold", TONE[status] ?? "bg-amber-50 text-amber-700")}>
      {label}
    </span>
  );
}

function ListCard<T>({ title, path, empty, render }: {
  title: string;
  path: string;
  empty: string;
  render: (item: T) => ReactNode;
}) {
  const { data, error, loading, reload } = useApi<T[]>(path);
  return (
    <section className="rounded-card border border-border bg-white p-5 shadow-soft sm:p-6">
      <h2 className="text-base font-bold text-ink">{title}</h2>
      {loading && !data ? (
        <div className="mt-4 space-y-3" aria-busy="true">
          {[0, 1, 2].map((i) => <div key={i} className="h-12 animate-pulse rounded-control bg-slate-100" />)}
        </div>
      ) : error ? (
        <p className="mt-4 text-sm text-red-600">
          {error.message || t.loadError}{" "}
          <button type="button" onClick={reload} className="font-semibold text-brand hover:underline">{t.retry}</button>
        </p>
      ) : !data?.length ? (
        <p className="mt-4 text-sm text-muted">{empty}</p>
      ) : (
        <ul className="mt-3 divide-y divide-border">{data.map(render)}</ul>
      )}
    </section>
  );
}

export function RecentPlans() {
  return (
    <ListCard<PlanOut>
      title={t.plans.title}
      path="/v1/plans?limit=10"
      empty={t.plans.empty}
      render={(p) => (
        <li key={p.id}>
          <Link
            href={`/reja/?id=${encodeURIComponent(p.id)}`}
            className="flex items-center gap-3 rounded-control px-2 py-3 hover:bg-canvas focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
          >
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold text-ink">{p.title}</span>
              <span className="text-xs text-muted">{formatDate(p.created_at)}</span>
            </span>
            <Badge status={p.status} label={t.plans.status[p.status as keyof typeof t.plans.status] ?? p.status} />
          </Link>
        </li>
      )}
    />
  );
}

export function RecentPayments() {
  return (
    <ListCard<PaymentOut>
      title={t.payments.title}
      path="/v1/payments?limit=10"
      empty={t.payments.empty}
      render={(p) => (
        <li key={p.id} className="flex items-center gap-3 px-2 py-3">
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-semibold text-ink">{p.title}</span>
            <span className="text-xs text-muted">
              {formatDate(p.created_at)} · {formatSom(p.amount_som)}
            </span>
            {p.admin_note && p.status === "rejected" ? (
              <span className="mt-0.5 block text-xs text-red-600">{p.admin_note}</span>
            ) : null}
          </span>
          <Badge status={p.status} label={t.payments.status[p.status as keyof typeof t.payments.status] ?? p.status} />
        </li>
      )}
    />
  );
}

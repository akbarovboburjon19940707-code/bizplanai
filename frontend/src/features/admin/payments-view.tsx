"use client";

import { useState } from "react";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { useApi } from "@/shared/api/use-api";
import { cn } from "@/shared/lib/cn";
import { formatDate, formatSom } from "@/shared/lib/format";
import { formatPhone } from "@/shared/lib/phone";
import { Button } from "@/shared/ui/button";
import { FormAlert } from "@/shared/ui/form-field";
import { LoadError } from "./admin-shell";
import { PaymentActionDialog } from "./payment-action-dialog";
import type { AdminPayment } from "./types";

const t = uz.admin.payments;
type Filter = keyof typeof t.filters;
const FILTERS = Object.keys(t.filters) as Filter[];
const PAGE = 50;
const STATUS_TONE: Record<string, string> = {
  paid: "bg-emerald-50 text-emerald-700",
  rejected: "bg-red-50 text-red-700",
  cancelled: "bg-slate-100 text-slate-700",
};
const providerLabel = (p: string) => uz.payments.providers[p as keyof typeof uz.payments.providers] ?? p;

export function PaymentsView() {
  const [filter, setFilter] = useState<Filter>("reviewing");
  const [limit, setLimit] = useState(PAGE);
  const [action, setAction] = useState<{ payment: AdminPayment; kind: "approve" | "reject" } | null>(null);
  const [notice, setNotice] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const qs = new URLSearchParams({ limit: String(limit) });
  if (filter !== "all") qs.set("status", filter);
  const list = useApi<AdminPayment[]>(`/v1/admin/payments?${qs.toString()}`);

  const openReceipt = async (p: AdminPayment) => {
    const tab = window.open("about:blank", "_blank"); // popup blokirovkasidan qochish uchun klik paytida
    try {
      const { url } = await apiRequest<{ url: string }>(`/v1/admin/payments/${encodeURIComponent(p.id)}/receipt`);
      if (tab) {
        tab.opener = null;
        tab.location.href = url;
      } else window.location.href = url;
    } catch (e) {
      tab?.close();
      setNotice({ tone: "error", text: e instanceof ApiError ? e.message : uz.authForms.genericError });
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2" role="group" aria-label={uz.admin.nav.payments}>
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            aria-pressed={filter === f}
            onClick={() => { setFilter(f); setLimit(PAGE); setNotice(null); }}
            className={cn(
              "rounded-full border px-3.5 py-1.5 text-sm font-semibold",
              filter === f ? "border-brand bg-brand text-white" : "border-border bg-white text-ink hover:border-blue-200",
            )}
          >
            {t.filters[f]}
          </button>
        ))}
      </div>
      {notice ? <FormAlert tone={notice.tone}>{notice.text}</FormAlert> : null}
      {list.error ? (
        <LoadError message={list.error.message} onRetry={list.reload} />
      ) : !list.data ? (
        <div className="space-y-3" aria-busy="true">{[0, 1, 2].map((i) => <div key={i} className="h-24 animate-pulse rounded-card bg-white" />)}</div>
      ) : list.data.length === 0 ? (
        <p className="text-sm text-muted">{uz.admin.empty}</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {list.data.map((p) => (
            <li key={p.id} className="flex flex-col gap-3 rounded-card border border-border bg-white p-4 shadow-soft md:flex-row md:items-center">
              <div className="min-w-0 flex-1">
                <p className="truncate font-semibold text-ink">{p.title}</p>
                <p className="text-sm text-muted">
                  {t.kinds[p.kind as keyof typeof t.kinds] ?? p.kind} · {t.provider}: {providerLabel(p.provider)} · {formatDate(p.created_at)} · <span className="font-mono text-xs">{p.id}</span>
                </p>
                <p className="mt-1 text-sm">
                  <span className="text-muted">{t.customer}: </span>
                  <span className="font-medium">{p.user_name || "—"}</span>{" "}
                  <span className="tabular-nums text-muted">{p.user_phone ? formatPhone(p.user_phone) : ""}</span>
                </p>
                {p.admin_note ? <p className="mt-1 text-xs text-muted">“{p.admin_note}”</p> : null}
              </div>
              <div className="flex flex-wrap items-center gap-2 md:justify-end">
                <span className="text-lg font-bold tabular-nums">{formatSom(p.amount_som)}</span>
                {p.has_receipt ? (
                  <Button size="sm" variant="outline" onClick={() => void openReceipt(p)}>{t.receipt}</Button>
                ) : p.provider === "manual" ? (
                  <span className="text-xs text-muted">{t.noReceipt}</span>
                ) : null}
                {p.provider === "manual" && (p.status === "reviewing" || p.status === "pending") ? (
                  <>
                    <Button size="sm" onClick={() => setAction({ payment: p, kind: "approve" })}>{t.approve}</Button>
                    <Button size="sm" variant="outline" className="text-red-700" onClick={() => setAction({ payment: p, kind: "reject" })}>{t.reject}</Button>
                  </>
                ) : (
                  <span className={cn("rounded-full px-2.5 py-1 text-xs font-semibold", STATUS_TONE[p.status] ?? "bg-amber-50 text-amber-800")}>
                    {uz.payments.status[p.status as keyof typeof uz.payments.status] ?? p.status}
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      {list.data && list.data.length >= limit ? (
        <Button variant="outline" className="self-center" onClick={() => setLimit((l) => l + PAGE)}>{uz.admin.more}</Button>
      ) : null}
      <PaymentActionDialog
        payment={action?.payment ?? null}
        action={action?.kind ?? "approve"}
        onClose={() => setAction(null)}
        onDone={() => {
          setNotice({ tone: "success", text: action?.kind === "reject" ? t.done.rejected : t.done.paid });
          setAction(null);
          list.reload();
        }}
      />
    </div>
  );
}

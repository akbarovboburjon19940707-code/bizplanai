"use client";

import Link from "next/link";
import { useState } from "react";
import { RequireAuth } from "@/features/auth/require-auth";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { cn } from "@/shared/lib/cn";
import { formatSom } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import { FormAlert } from "@/shared/ui/form-field";
import { ManualCheckoutPanel } from "./manual-checkout";
import { isManual, type PaymentOut } from "./types";
import { usePayment, usePaymentId } from "./use-payment";
import { openDownload } from "@/shared/lib/download";

const t = uz.payments;
type Status = Exclude<keyof typeof t.status, "title">;
const STATUSES: readonly Status[] = ["pending", "reviewing", "paid", "cancelled", "rejected"];

const TONE: Record<Status, string> = {
  pending: "bg-amber-50 text-amber-800",
  reviewing: "bg-blue-50 text-blue-800",
  paid: "bg-emerald-50 text-emerald-800",
  cancelled: "bg-slate-100 text-slate-700",
  rejected: "bg-red-50 text-red-700",
};

function NextAction({ payment }: { payment: PaymentOut }) {
  const [error, setError] = useState<string | null>(null);
  if (payment.kind === "catalog" && payment.target_id) {
    const download = async () => {
      try {
        const { url } = await apiRequest<{ url: string }>(
          `/v1/catalog/products/${encodeURIComponent(payment.target_id!)}/download`,
        );
        await openDownload(url, `${payment.title}.pdf`);
      } catch (e) {
        setError(e instanceof ApiError ? e.message : uz.authForms.genericError);
      }
    };
    return (
      <div className="flex flex-col gap-3">
        <Button size="lg" onClick={() => void download()} className="self-start">{t.next.catalog}</Button>
        {error ? <FormAlert>{error}</FormAlert> : null}
      </div>
    );
  }
  return (
    <div className="flex flex-wrap gap-3">
      <Button asChild size="lg"><Link href="/dashboard/">{t.next.subscription}</Link></Button>
      <Button asChild size="lg" variant="outline"><Link href="/kabinet/">{t.next.account}</Link></Button>
    </div>
  );
}

function PaymentView() {
  const id = usePaymentId();
  const { data, error, slow, savedCheckout, replacePayment } = usePayment(id);

  if (!id || (error && !data && error.status === 404)) {
    return <p className="text-sm text-red-600">{error?.message || t.notFound}</p>;
  }
  if (!data) {
    return error ? (
      <p className="text-sm text-red-600">{error.message || t.loadError}</p>
    ) : (
      <div className="space-y-3" aria-busy="true">
        <div className="h-6 w-48 animate-pulse rounded bg-slate-200" />
        <div className="h-24 animate-pulse rounded-control bg-slate-100" />
      </div>
    );
  }

  const p = data.payment;
  const status: Status = (STATUSES as readonly string[]).includes(p.status) ? (p.status as Status) : "pending";
  const showManual = p.provider === "manual" && (status === "pending" || status === "reviewing");
  const saved = savedCheckout ?? undefined;
  const checkout = isManual(data.checkout) ? data.checkout : isManual(saved) ? saved : null;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <p className="text-sm text-muted">{p.title}</p>
        <p className="mt-1 text-2xl font-bold tabular-nums text-ink">{formatSom(p.amount_som)}</p>
      </div>
      <div className={cn("rounded-control px-4 py-3", TONE[status])} role="status" aria-live="polite">
        <p className="font-semibold">{t.status[status]}</p>
        <p className="mt-0.5 text-sm">
          {status === "pending" && slow ? t.statusText.pendingSlow : t.statusText[status]}
          {status === "rejected" && p.admin_note ? ` ${p.admin_note}` : ""}
        </p>
      </div>
      {showManual ? <ManualCheckoutPanel payment={p} checkout={checkout} onUploaded={replacePayment} /> : null}
      {status === "paid" ? <NextAction payment={p} /> : null}
      {status === "cancelled" || status === "rejected" ? (
        <Button asChild variant="outline" className="self-start">
          <Link href={p.kind === "catalog" ? "/katalog/" : "/tariflar/"}>{uz.navigation[p.kind === "catalog" ? "catalog" : "tariffs"]}</Link>
        </Button>
      ) : null}
    </div>
  );
}

export function PaymentStatusPage() {
  return (
    <section className="mx-auto max-w-xl px-4 py-10 sm:px-6">
      <div className="rounded-card border border-border bg-white p-6 shadow-soft sm:p-8">
        <h1 className="mb-5 font-[var(--font-outfit)] text-2xl font-bold text-ink">{t.status.title}</h1>
        <RequireAuth fallback={<div className="h-32 animate-pulse rounded-control bg-slate-100" aria-busy="true" />}>
          <PaymentView />
        </RequireAuth>
      </div>
    </section>
  );
}

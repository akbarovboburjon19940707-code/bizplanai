"use client";

import { useState } from "react";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { useApi } from "@/shared/api/use-api";
import { FormAlert } from "@/shared/ui/form-field";
import { Modal } from "@/shared/ui/modal";
import { PROVIDERS, isTrustedCheckoutUrl, type PaymentEnvelope, type PaymentKind, type Provider } from "./types";

const t = uz.payments;

/**
 * To'lov usulini tanlash oynasi. Summa yuborilmaydi (server hisoblaydi).
 * Click/Payme -> ularning sahifasi; karta -> /tolov/{id} (karta raqami va chek yuklash shu yerda).
 */
export function PaymentDialog({ open, onClose, kind, targetId, title, onError }: {
  open: boolean;
  onClose: () => void;
  kind: PaymentKind;
  targetId?: string;
  title: string;
  /** Maxsus xatolarni (masalan `already_owned`) chaqiruvchi o'zi hal qiladi; true qaytarsa oyna yopiladi. */
  onError?: (error: ApiError) => boolean;
}) {
  const methods = useApi<Record<Provider, boolean>>(open ? "/v1/payments/methods" : null);
  const [busy, setBusy] = useState<Provider | null>(null);
  const [error, setError] = useState<string | null>(null);
  const enabled = PROVIDERS.filter((p) => methods.data?.[p]);

  const pay = async (provider: Provider) => {
    setBusy(provider);
    setError(null);
    try {
      const res = await apiRequest<PaymentEnvelope>("/v1/payments", {
        method: "POST",
        body: JSON.stringify({ kind, target_id: targetId ?? null, provider }),
      });
      const checkout = res.checkout;
      if ("type" in checkout && checkout.type === "redirect") {
        if (!isTrustedCheckoutUrl(checkout.url)) throw new ApiError(0, "bad_checkout", t.noMethods);
        window.location.href = checkout.url;
        return; // sahifa almashguncha tugma band bo'lib turadi
      }
      // /tolov/* static rewrite orqali beriladi: client navigatsiya emas, to'liq yuklash (ortiqcha RSC so'rovisiz)
      window.location.assign(`/tolov/${encodeURIComponent(res.payment.id)}/`);
    } catch (e) {
      setBusy(null);
      if (e instanceof ApiError && onError?.(e)) return onClose();
      setError(e instanceof ApiError && e.message ? e.message : uz.authForms.genericError);
    }
  };

  return (
    <Modal open={open} onClose={() => !busy && onClose()} title={t.dialogTitle} closeLabel={t.close}>
      <p className="text-sm font-semibold text-ink">{title}</p>
      <p className="mt-1 text-xs text-muted">{t.amountNote}</p>
      <div className="mt-4 flex flex-col gap-3" aria-busy={methods.loading || !!busy}>
        {error ? <FormAlert>{error}</FormAlert> : null}
        {methods.loading ? (
          [0, 1].map((i) => <div key={i} className="h-16 animate-pulse rounded-control bg-slate-100" />)
        ) : methods.error ? (
          <FormAlert>{methods.error.message || t.noMethods}</FormAlert>
        ) : enabled.length === 0 ? (
          <FormAlert tone="info">{t.noMethods}</FormAlert>
        ) : (
          enabled.map((p) => (
            <button
              key={p}
              type="button"
              disabled={!!busy}
              onClick={() => void pay(p)}
              className="flex items-center gap-3 rounded-control border border-border px-4 py-3 text-left transition hover:border-brand hover:bg-blue-50/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand disabled:opacity-60"
            >
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-semibold text-ink">{t.providers[p]}</span>
                <span className="block text-xs text-muted">{t.providerHint[p]}</span>
              </span>
              {busy === p ? (
                <span className="size-4 animate-spin rounded-full border-2 border-brand border-t-transparent" aria-label={t.creating} />
              ) : (
                <span aria-hidden="true" className="text-muted">→</span>
              )}
            </button>
          ))
        )}
      </div>
    </Modal>
  );
}

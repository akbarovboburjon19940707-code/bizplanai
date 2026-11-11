"use client";

import { useRef, useState } from "react";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { formatSom } from "@/shared/lib/format";
import { useCopy } from "@/shared/lib/use-copy";
import { Button } from "@/shared/ui/button";
import { FormAlert } from "@/shared/ui/form-field";
import { checkReceipt } from "./receipt";
import type { ManualCheckout, PaymentOut } from "./types";

const t = uz.payments;

function CopyRow({ label, value }: { label: string; value: string }) {
  const { copied, copy } = useCopy();
  return (
    <div className="flex items-center justify-between gap-3 rounded-control bg-canvas px-4 py-3">
      <div className="min-w-0">
        <p className="text-xs text-muted">{label}</p>
        <p className="truncate font-mono text-base font-semibold tracking-wider text-ink">{value}</p>
      </div>
      <Button type="button" size="sm" variant="outline" onClick={() => void copy(value.replace(/\s/g, ""))} aria-live="polite">
        {copied ? t.manual.copied : t.manual.copy}
      </Button>
    </div>
  );
}

/** Karta rekvizitlari va chek yuklash. Yuklangach to'lov `reviewing` ga o'tadi. */
export function ManualCheckoutPanel({ payment, checkout, onUploaded }: {
  payment: PaymentOut;
  checkout: ManualCheckout | null;
  onUploaded: (p: PaymentOut) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const pick = (f: File | undefined) => {
    setError(null);
    if (!f) return setFile(null);
    const problem = checkReceipt(f);
    if (problem) {
      setFile(null);
      if (input.current) input.current.value = "";
      return setError(t.receipt[problem]);
    }
    setFile(f);
  };

  const upload = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const body = new FormData();
      body.append("file", file);
      onUploaded(await apiRequest<PaymentOut>(`/v1/payments/${encodeURIComponent(payment.id)}/receipt`, { method: "POST", body }));
    } catch (e) {
      setError(e instanceof ApiError && e.message ? e.message : uz.authForms.genericError);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {checkout ? (
        <>
          <h2 className="text-base font-bold text-ink">{t.manual.title}</h2>
          <ol className="list-decimal space-y-1 pl-5 text-sm text-muted">
            {t.manual.steps.map((s) => <li key={s}>{s}</li>)}
          </ol>
          <CopyRow label={t.manual.card} value={checkout.card_number} />
          {checkout.card_holder ? <p className="text-sm text-muted">{t.manual.holder}: <span className="font-semibold text-ink">{checkout.card_holder}</span></p> : null}
          <CopyRow label={t.amount} value={formatSom(checkout.amount_som)} />
        </>
      ) : null}
      <div className="flex flex-col gap-2">
        <label htmlFor="receipt" className="text-sm font-medium text-ink">{t.receipt.label}</label>
        <input
          ref={input}
          id="receipt"
          type="file"
          accept="image/jpeg,image/png,image/webp,application/pdf"
          onChange={(e) => pick(e.target.files?.[0])}
          aria-describedby="receipt-hint"
          className="block w-full text-sm text-muted file:mr-3 file:rounded-control file:border file:border-border file:bg-white file:px-4 file:py-2 file:text-sm file:font-semibold file:text-ink hover:file:bg-canvas"
        />
        <p id="receipt-hint" className="text-xs text-muted">{t.receipt.hint}</p>
      </div>
      {error ? <FormAlert>{error}</FormAlert> : null}
      <Button type="button" onClick={() => void upload()} disabled={!file || busy} className="self-start">
        {busy ? t.receipt.uploading : payment.status === "reviewing" ? t.receipt.replace : t.receipt.upload}
      </Button>
    </div>
  );
}

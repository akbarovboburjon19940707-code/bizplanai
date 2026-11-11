"use client";

import { useState } from "react";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { formatSom } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import { FormAlert, inputClass } from "@/shared/ui/form-field";
import { Modal } from "@/shared/ui/modal";
import type { AdminPayment } from "./types";

const t = uz.admin.payments;

/** Tasdiqlash yoki rad etish: izoh bilan, ikki marta bosishdan himoyalangan. */
export function PaymentActionDialog({ payment, action, onClose, onDone }: {
  payment: AdminPayment | null;
  action: "approve" | "reject";
  onClose: () => void;
  onDone: () => void;
}) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reject = action === "reject";

  const submit = async () => {
    if (!payment) return;
    setBusy(true);
    setError(null);
    try {
      await apiRequest(`/v1/admin/payments/${encodeURIComponent(payment.id)}/${action}`, {
        method: "POST",
        body: JSON.stringify({ note: note.trim() || null }),
      });
      setNote("");
      onDone();
    } catch (e) {
      setError(e instanceof ApiError && e.message ? e.message : uz.authForms.genericError);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={!!payment} onClose={() => !busy && onClose()} title={reject ? t.reject : t.approve} closeLabel={t.cancel}>
      {payment ? (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-ink">{reject ? t.confirmReject : t.confirmApprove}</p>
          <p className="rounded-control bg-canvas px-3 py-2 text-sm">
            <span className="font-semibold">{payment.title}</span> · {formatSom(payment.amount_som)}
            <br />
            <span className="text-muted">{payment.user_name || "—"} · {payment.user_phone || payment.user_id}</span>
          </p>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="admin-note" className="text-sm font-medium">{reject ? t.rejectNote : t.note}</label>
            <textarea id="admin-note" rows={3} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} className={inputClass} />
          </div>
          {error ? <FormAlert>{error}</FormAlert> : null}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose} disabled={busy}>{t.cancel}</Button>
            <Button onClick={() => void submit()} disabled={busy} className={reject ? "bg-red-600 hover:bg-red-700" : undefined}>
              {reject ? t.reject : t.approve}
            </Button>
          </div>
        </div>
      ) : null}
    </Modal>
  );
}

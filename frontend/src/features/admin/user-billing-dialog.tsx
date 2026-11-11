"use client";

import { useEffect, useState } from "react";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { useApi } from "@/shared/api/use-api";
import { cn } from "@/shared/lib/cn";
import { formatDate } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import { FormAlert, FormField, inputClass } from "@/shared/ui/form-field";
import { Modal } from "@/shared/ui/modal";
import type { AdminUserRow, UserBilling } from "./types";

const t = uz.admin.billing;

/** Admin: foydalanuvchiga tarif yoki kredit berish, obunani bekor qilish. Har amal serverda audit bilan yoziladi. */
export function UserBillingDialog({ user, onClose, onChanged }: {
  user: AdminUserRow | null;
  onClose: () => void;
  onChanged: (credits: number) => void;
}) {
  const billing = useApi<UserBilling>(user ? `/v1/admin/users/${encodeURIComponent(user.id)}/billing` : null);
  const [data, setData] = useState<UserBilling | null>(null);
  const [tariff, setTariff] = useState("");
  const [days, setDays] = useState("30");
  const [note, setNote] = useState("");
  const [count, setCount] = useState("1");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    setData(billing.data ?? null);
    const first = billing.data?.tariffs[0];
    if (first) {
      setTariff((cur) => cur || first.code);
      setDays((cur) => (cur === "30" ? String(first.duration_days) : cur));
    }
  }, [billing.data]);
  useEffect(() => { setNotice(null); setNote(""); setCount("1"); setTariff(""); setDays("30"); }, [user?.id]);

  const call = async (path: string, body: object, confirmText?: string) => {
    if (confirmText && !window.confirm(confirmText)) return;
    setBusy(true);
    setNotice(null);
    try {
      const res = await apiRequest<UserBilling>(path, { method: "POST", body: JSON.stringify(body) });
      setData(res);
      onChanged(res.user.plan_credits);
      setNotice({ ok: true, text: t.done });
      setNote("");
    } catch (e) {
      setNotice({ ok: false, text: e instanceof ApiError && e.message ? e.message : uz.authForms.genericError });
    } finally {
      setBusy(false);
    }
  };

  const name = user ? [user.first_name, user.last_name].filter(Boolean).join(" ") || user.phone || user.id : "";
  const daysNum = Number(days);
  const countNum = Number(count);
  const base = user ? `/v1/admin/users/${encodeURIComponent(user.id)}` : "";

  return (
    <Modal open={!!user} onClose={() => !busy && onClose()} title={t.title(name)} closeLabel={t.close}>
      {billing.error ? <FormAlert>{billing.error.message}</FormAlert> : !data ? (
        <div className="h-40 animate-pulse rounded-control bg-slate-100" aria-busy="true" />
      ) : (
        <div className="flex max-h-[70vh] flex-col gap-5 overflow-y-auto pr-1">
          {notice ? <FormAlert tone={notice.ok ? "success" : "error"}>{notice.text}</FormAlert> : null}
          <section>
            <h3 className="text-sm font-semibold text-ink">{t.current}</h3>
            {data.subscriptions.length === 0 ? <p className="mt-1 text-sm text-muted">{t.none}</p> : (
              <ul className="mt-2 flex flex-col gap-2">
                {data.subscriptions.map((s) => (
                  <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 rounded-control border border-border px-3 py-2 text-sm">
                    <span>
                      <span className="font-semibold">{s.tariff_name}</span>{" "}
                      <span className={cn("text-xs", s.status === "active" ? "text-emerald-700" : "text-muted")}>
                        {t.status[s.status as keyof typeof t.status] ?? s.status}
                      </span>
                      <span className="block text-xs text-muted">
                        {t.until(formatDate(s.ends_at))} · {t.source[s.source as keyof typeof t.source] ?? s.source}
                      </span>
                    </span>
                    {s.status === "active" ? (
                      <Button type="button" size="sm" variant="outline" className="text-red-700" disabled={busy}
                        onClick={() => void call(`/v1/admin/subscriptions/${encodeURIComponent(s.id)}/revoke`, { note }, t.confirmRevoke)}>
                        {t.revoke}
                      </Button>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-2 text-sm text-ink">{t.credits(data.user.plan_credits)}</p>
          </section>

          <FormField id="grant-note" label={t.note}>
            <input id="grant-note" className={inputClass} maxLength={300} value={note} onChange={(e) => setNote(e.target.value)} />
          </FormField>

          <form className="flex flex-col gap-2" onSubmit={(e) => {
            e.preventDefault();
            void call(`${base}/grant`, { kind: "subscription", tariff_code: tariff, days: daysNum, note });
          }}>
            <h3 className="text-sm font-semibold text-ink">{t.grantSub}</h3>
            <div className="grid grid-cols-[1fr_6rem_auto] items-end gap-2">
              <FormField id="grant-tariff" label={t.tariff}>
                <select id="grant-tariff" className={inputClass} value={tariff} onChange={(e) => {
                  setTariff(e.target.value);
                  const d = data.tariffs.find((x) => x.code === e.target.value)?.duration_days;
                  if (d) setDays(String(d));
                }}>
                  {data.tariffs.map((x) => <option key={x.code} value={x.code}>{x.name}</option>)}
                </select>
              </FormField>
              <FormField id="grant-days" label={t.days}>
                <input id="grant-days" className={`${inputClass} text-right tabular-nums`} inputMode="numeric" value={days}
                  onChange={(e) => setDays(e.target.value.replace(/\D/g, "").slice(0, 3))} />
              </FormField>
              <Button type="submit" disabled={busy || !tariff || !(daysNum >= 1 && daysNum <= 366)}>{t.give}</Button>
            </div>
          </form>

          <form className="flex flex-col gap-2" onSubmit={(e) => {
            e.preventDefault();
            void call(`${base}/grant`, { kind: "credits", count: countNum, note });
          }}>
            <h3 className="text-sm font-semibold text-ink">{t.grantCredits}</h3>
            <div className="grid grid-cols-[1fr_auto] items-end gap-2">
              <FormField id="grant-count" label={t.count}>
                <input id="grant-count" className={`${inputClass} text-right tabular-nums`} inputMode="numeric" value={count}
                  onChange={(e) => setCount(e.target.value.replace(/\D/g, "").slice(0, 2))} />
              </FormField>
              <Button type="submit" disabled={busy || !(countNum >= 1 && countNum <= 20)}>{t.give}</Button>
            </div>
          </form>

          {data.grants.length ? (
            <section>
              <h3 className="text-sm font-semibold text-ink">{t.history}</h3>
              <ul className="mt-2 flex flex-col gap-1 text-xs text-muted">
                {data.grants.map((g) => (
                  <li key={g.id}>
                    {formatDate(g.created_at)} · {g.title} · {t.grantStatus[g.status as keyof typeof t.grantStatus] ?? g.status}
                    {g.note ? ` · ${g.note}` : ""}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>
      )}
    </Modal>
  );
}

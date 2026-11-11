"use client";

import { useState } from "react";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { useApi } from "@/shared/api/use-api";
import { cn } from "@/shared/lib/cn";
import { formatDate } from "@/shared/lib/format";
import { formatPhone } from "@/shared/lib/phone";
import { Button } from "@/shared/ui/button";
import { FormAlert, inputClass } from "@/shared/ui/form-field";
import { LoadError } from "./admin-shell";
import type { AdminMessage } from "./types";

const t = uz.admin.messages;
const topics = uz.contact.topics as Record<string, string>;
type Filter = keyof typeof t.filters;
const FILTERS = Object.keys(t.filters) as Filter[];
const PAGE = 50;

function MessageCard({ m, onDone }: { m: AdminMessage; onDone: () => void }) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const markDone = async () => {
    setBusy(true);
    setError(null);
    try {
      await apiRequest(`/v1/admin/messages/${encodeURIComponent(m.id)}/done`, { method: "POST", body: JSON.stringify({ note }) });
      onDone();
    } catch (e) {
      setError(e instanceof ApiError && e.message ? e.message : uz.authForms.genericError);
    } finally {
      setBusy(false);
    }
  };
  return (
    <li className="rounded-card border border-border bg-white p-4 shadow-soft sm:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-semibold text-ink">
          {m.name}
          {m.user_id ? <span className="ml-2 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-brand">{t.registered}</span> : null}
        </p>
        <p className="text-xs text-muted">{formatDate(m.created_at)} · {topics[m.topic] ?? m.topic}</p>
      </div>
      <a href={`tel:${m.phone}`} className="mt-1 inline-block text-sm font-semibold tabular-nums text-brand hover:underline">
        {formatPhone(m.phone)}
      </a>
      <p className="mt-3 whitespace-pre-wrap break-words text-sm text-ink">{m.message}</p>
      {error ? <div className="mt-3"><FormAlert>{error}</FormAlert></div> : null}
      {m.status === "new" ? (
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <label htmlFor={`note-${m.id}`} className="sr-only">{t.note}</label>
          <input id={`note-${m.id}`} className={cn(inputClass, "sm:flex-1")} maxLength={500} placeholder={t.note}
            value={note} onChange={(e) => setNote(e.target.value)} />
          <Button type="button" onClick={() => void markDone()} disabled={busy}>{t.markDone}</Button>
        </div>
      ) : m.admin_note ? (
        <p className="mt-3 text-xs text-muted"><span className="font-semibold">{t.noteLabel}:</span> {m.admin_note}</p>
      ) : null}
    </li>
  );
}

/** Admin > Murojaatlar: aloqa formasidan kelgan xabarlar, "javob berildi" belgisi bilan. */
export function MessagesView() {
  const [filter, setFilter] = useState<Filter>("new");
  const [limit, setLimit] = useState(PAGE);
  const [notice, setNotice] = useState(false);
  const qs = new URLSearchParams({ limit: String(limit) });
  if (filter !== "all") qs.set("status", filter);
  const list = useApi<AdminMessage[]>(`/v1/admin/messages?${qs.toString()}`);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2" role="group" aria-label={uz.admin.nav.messages}>
        {FILTERS.map((f) => (
          <button key={f} type="button" aria-pressed={filter === f}
            onClick={() => { setFilter(f); setLimit(PAGE); setNotice(false); }}
            className={cn("rounded-full border px-3.5 py-1.5 text-sm font-semibold",
              filter === f ? "border-brand bg-brand text-white" : "border-border bg-white text-ink hover:border-blue-200")}>
            {t.filters[f]}
          </button>
        ))}
      </div>
      {notice ? <FormAlert tone="success">{t.done}</FormAlert> : null}
      {list.error ? (
        <LoadError message={list.error.message} onRetry={list.reload} />
      ) : !list.data ? (
        <div className="space-y-3" aria-busy="true">{[0, 1, 2].map((i) => <div key={i} className="h-28 animate-pulse rounded-card bg-white" />)}</div>
      ) : list.data.length === 0 ? (
        <p className="text-sm text-muted">{uz.admin.empty}</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {list.data.map((m) => (
            <MessageCard key={m.id} m={m} onDone={() => { setNotice(true); list.reload(); }} />
          ))}
        </ul>
      )}
      {list.data && list.data.length >= limit ? (
        <Button variant="outline" className="self-center" onClick={() => setLimit((l) => l + PAGE)}>{uz.admin.more}</Button>
      ) : null}
    </div>
  );
}

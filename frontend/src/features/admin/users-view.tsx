"use client";

import { useState } from "react";
import { uz } from "@/messages/uz";
import { useApi } from "@/shared/api/use-api";
import { formatPhone } from "@/shared/lib/phone";
import { Button } from "@/shared/ui/button";
import { inputClass } from "@/shared/ui/form-field";
import { LoadError } from "./admin-shell";
import type { AdminUserRow } from "./types";
import { useDebouncedSearch } from "./use-debounced-search";

const t = uz.admin.users;
const PAGE = 50;

export function UsersView() {
  const search = useDebouncedSearch();
  const [limit, setLimit] = useState(PAGE);
  const qs = new URLSearchParams({ limit: String(limit) });
  if (search.query) qs.set("q", search.query);
  const list = useApi<AdminUserRow[]>(`/v1/admin/users?${qs.toString()}`);

  return (
    <div className="flex flex-col gap-4">
      <div className="max-w-md">
        <label htmlFor="admin-users-q" className="sr-only">{uz.admin.search}</label>
        <input id="admin-users-q" type="search" maxLength={100} value={search.input} placeholder={t.placeholder}
          onChange={(e) => { search.setInput(e.target.value); setLimit(PAGE); }} className={inputClass} />
      </div>
      {list.error ? (
        <LoadError message={list.error.message} onRetry={list.reload} />
      ) : !list.data ? (
        <div className="h-64 animate-pulse rounded-card bg-white" aria-busy="true" />
      ) : list.data.length === 0 ? (
        <p className="text-sm text-muted">{uz.admin.empty}</p>
      ) : (
        <div className="overflow-x-auto rounded-card border border-border bg-white shadow-soft">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead className="border-b border-border bg-canvas text-xs uppercase tracking-wide text-muted">
              <tr>
                <th scope="col" className="px-4 py-3">{t.phone}</th>
                <th scope="col" className="px-4 py-3">{t.name}</th>
                <th scope="col" className="px-4 py-3">{t.telegram}</th>
                <th scope="col" className="px-4 py-3">{t.role}</th>
                <th scope="col" className="px-4 py-3 text-right">{t.credits}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {list.data.map((u) => (
                <tr key={u.id}>
                  <td className="px-4 py-3 tabular-nums">{u.phone ? formatPhone(u.phone) : "—"}</td>
                  <td className="px-4 py-3">{[u.first_name, u.last_name].filter(Boolean).join(" ") || "—"}</td>
                  <td className="px-4 py-3">{u.telegram_username ? `@${u.telegram_username}` : "—"}</td>
                  <td className="px-4 py-3">
                    {u.role === "admin" ? <span className="rounded-full bg-violet-50 px-2 py-0.5 text-xs font-semibold text-violet-700">{t.admin}</span> : t.user}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">{u.plan_credits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {list.data && list.data.length >= limit ? (
        <Button variant="outline" className="self-center" onClick={() => setLimit((l) => l + PAGE)}>{uz.admin.more}</Button>
      ) : null}
    </div>
  );
}

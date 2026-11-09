"use client";

import { useState } from "react";
import { uz } from "@/messages/uz";
import { cn } from "@/shared/lib/cn";
import { formatNumber, formatSom } from "@/shared/lib/format";
import type { PreviewState } from "./use-preview";

const t = uz.plans.result;

type Table = { ilova: string; title: string; headers: string[]; rows: (string | number | null)[][] };

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function years(v: number | null) {
  return v && v > 0 ? `${v.toFixed(1)} ${t.years}` : "10+ yil";
}

export function IndicatorCards({ state }: { state: PreviewState }) {
  if (state.status === "incomplete") {
    return <p className="rounded-card border border-dashed border-border bg-white p-4 text-sm text-muted">{t.fillRequired}</p>;
  }
  const data = "data" in state ? state.data : null;
  const ind = (data?.indicators ?? {}) as Record<string, unknown>;
  const npv = num(ind.npv);
  const irr = num(ind.irr);
  const bep = num(ind.zararsizlik_nuqtasi);
  const dscr = num(ind.dscr_min);
  const items = [
    { label: t.npv, value: formatSom(npv), tone: npv !== null && npv < 0 ? "bad" : "good" },
    { label: t.irr, value: irr ? `${irr.toFixed(1)}%` : "—" },
    { label: t.payback, value: years(num(ind.payback)) },
    { label: t.dpp, value: years(num(ind.dpp)) },
    { label: t.pi, value: num(ind.pi)?.toFixed(2) ?? "—" },
    { label: t.dscr, value: dscr !== null ? dscr.toFixed(2) : "—", tone: dscr !== null && dscr < 1.2 ? "bad" : undefined },
    { label: t.breakeven, value: bep !== null ? `${bep.toFixed(1)}%` : "—" },
  ];
  const warning = typeof ind.warning === "string" ? ind.warning : "";
  return (
    <div aria-live="polite" aria-busy={state.status === "loading"}>
      <div className={cn("grid grid-cols-2 gap-2 transition-opacity", state.status === "loading" && "opacity-60")}>
        {items.map((it) => (
          <div key={it.label} className="rounded-control border border-border bg-white p-3">
            <div className="text-xs text-muted">{it.label}</div>
            <div
              className={cn(
                "mt-1 text-sm font-bold tabular-nums",
                it.tone === "bad" ? "text-red-600" : it.tone === "good" ? "text-emerald-700" : "text-ink",
              )}
            >
              {data ? it.value : "…"}
            </div>
          </div>
        ))}
      </div>
      {state.status === "loading" ? <p className="mt-2 text-xs text-muted">{t.calculating}</p> : null}
      {state.status === "error" ? <p className="mt-2 text-xs text-red-600">{state.message}</p> : null}
      {warning ? <p className="mt-3 rounded-control bg-amber-50 p-3 text-xs text-amber-800">{warning}</p> : null}
    </div>
  );
}

export function PreviewTables({ state }: { state: PreviewState }) {
  const data = "data" in state ? state.data : null;
  const tables = (data?.tables ?? []) as unknown as Table[];
  const [active, setActive] = useState(0);
  if (!tables.length) return null;
  const tbl = tables[Math.min(active, tables.length - 1)];
  return (
    <section className="rounded-card border border-border bg-white p-4 shadow-sm sm:p-6">
      <h2 className="font-[var(--font-outfit)] text-lg font-bold text-ink">{t.tables}</h2>
      <label className="mt-3 block text-sm">
        <span className="sr-only">{t.tables}</span>
        <select
          className="w-full rounded-control border border-border bg-white px-3 py-2 text-sm"
          value={active}
          onChange={(e) => setActive(Number(e.target.value))}
        >
          {tables.map((x, i) => (
            <option key={`${x.ilova}-${i}`} value={i}>
              {x.ilova}: {x.title}
            </option>
          ))}
        </select>
      </label>
      <div className="mt-3 max-h-[28rem] overflow-auto rounded-control border border-border">
        <table className="min-w-full text-xs">
          <thead className="sticky top-0 bg-brand-dark text-white">
            <tr>
              {tbl.headers.map((h, i) => (
                <th key={i} scope="col" className="whitespace-nowrap px-2 py-2 text-left font-semibold">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tbl.rows.map((row, r) => (
              <tr key={r} className={cn("border-t border-border", /^(JAMI|SOF|TANNARX|LOYIHA)/.test(String(row[0])) && "bg-amber-50 font-semibold")}>
                {row.map((cell, c) => (
                  <td key={c} className={cn("whitespace-nowrap px-2 py-1.5", c > 0 && "text-right tabular-nums")}>
                    {typeof cell === "number" ? formatNumber(cell) : (cell ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

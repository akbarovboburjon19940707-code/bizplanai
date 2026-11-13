import { uz } from "@/messages/uz";

const p = uz.home.preview;

/** Bosh sahifa hero: natija namunasi (Word sahifasi + Excel jadvali). Dekorativ, ekran o'qigichdan yashirin. */
export function HeroArt() {
  return (
    <div aria-hidden="true" className="relative mx-auto mt-12 hidden h-[460px] w-full max-w-[520px] select-none lg:mt-0 lg:block">
      <span className="absolute left-3 top-0 rounded-full bg-amber-100 px-3 py-1 text-[11px] font-semibold text-amber-800">{p.sample}</span>
      {/* Excel */}
      <div className="absolute right-0 top-6 w-[78%] rotate-[3deg] rounded-2xl border border-border bg-white p-4 shadow-lift">
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-emerald-700">
          <span className="grid size-6 place-items-center rounded bg-emerald-600 text-[10px] font-bold text-white">X</span>{p.excelName}
        </div>
        <table className="w-full text-[11px] tabular-nums">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="p-1.5 text-left font-medium">{p.unit}</th>
              {[1, 2, 3].map((y) => <th key={y} className="p-1.5 text-right font-medium">{p.year(y)}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {p.rows.map((r) => (
              <tr key={r.label} className={"total" in r ? "font-semibold text-emerald-700" : undefined}>
                <td className="p-1.5">{r.label}</td>
                {r.values.map((v, i) => <td key={i} className="p-1.5 text-right">{v}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Word */}
      <div className="absolute left-0 top-28 w-[70%] -rotate-2 rounded-2xl border border-border bg-white p-5 shadow-lift">
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-brand">
          <span className="grid size-6 place-items-center rounded bg-brand text-[10px] font-bold text-white">W</span>{p.wordName}
        </div>
        <div className="text-center">
          <div className="text-[10px] uppercase tracking-widest text-muted">{p.docKind}</div>
          <div className="mt-1 font-[var(--font-outfit)] text-base font-bold text-ink">{p.docTitle}</div>
          <div className="mx-auto mt-2 h-px w-16 bg-slate-200" />
        </div>
        <div className="mt-3 space-y-1.5">
          <div className="h-1.5 w-full rounded bg-slate-100" /><div className="h-1.5 w-11/12 rounded bg-slate-100" /><div className="h-1.5 w-4/5 rounded bg-slate-100" />
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2 text-center">
          {p.metrics.map(([k, v]) => (
            <div key={k} className="rounded-lg bg-blue-50 p-2">
              <div className="text-[9px] text-muted">{k}</div>
              <div className="text-sm font-bold text-ink">{v}</div>
            </div>
          ))}
        </div>
        <div className="mt-3 space-y-1.5"><div className="h-1.5 w-full rounded bg-slate-100" /><div className="h-1.5 w-3/4 rounded bg-slate-100" /></div>
      </div>
      <div className="absolute bottom-2 right-6 flex items-center gap-3 rounded-2xl border border-border bg-white px-4 py-3 shadow-soft">
        <div className="grid size-9 place-items-center rounded-full bg-emerald-100 font-bold text-emerald-700">✓</div>
        <div><div className="text-sm font-semibold text-ink">{p.ready}</div><div className="text-xs text-muted">{p.readyText}</div></div>
      </div>
    </div>
  );
}

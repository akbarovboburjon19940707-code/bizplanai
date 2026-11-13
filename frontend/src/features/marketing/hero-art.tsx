/** Bosh sahifa hero bezagi (dekorativ, ekran o'qigichdan yashirin). */
export function HeroArt() {
  return (
    <div aria-hidden="true" className="mt-14 hidden lg:block">
      <div className="relative mx-auto aspect-square max-w-[420px] rounded-[2rem] bg-gradient-to-br from-slate-900 via-blue-900 to-blue-600 p-8 shadow-soft">
        <div className="absolute -right-5 -top-5 size-24 rounded-3xl bg-violet-400/80 blur-2xl" />
        <div className="relative flex h-full flex-col justify-between gap-4 overflow-hidden rounded-3xl border border-white/20 bg-white/10 p-6 backdrop-blur-sm">
          <div className="space-y-1">
            <div className="text-sm font-semibold text-white">Namuna: non sexi</div>
            <div className="text-xs text-blue-100">Kredit 300 mln so‘m, 3 yil</div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              ["NPV", "186 mln"],
              ["ROI", "41%"],
              ["Yillik tushum", "1,2 mlrd"],
              ["Qoplash", "2,3 yil"],
            ].map(([item, value], index) => (
              <div key={item} className="rounded-2xl border border-white/15 bg-white/10 p-3">
                <div className="text-xs text-blue-100">{item}</div>
                <div className="mt-1 font-[var(--font-outfit)] text-lg font-bold tabular-nums text-white">{value}</div>
                <div className={`mt-3 h-1.5 rounded-full ${index % 2 ? "bg-emerald-300" : "bg-violet-300"}`} />
              </div>
            ))}
          </div>
          <div className="h-20 shrink-0 rounded-2xl border border-white/15 bg-white/10 p-3">
            <div className="text-[11px] text-blue-100">Pul oqimi, oylar</div>
            <div className="mt-2 flex h-10 items-end gap-2">
              {[34, 58, 43, 75, 61, 90, 70].map((height, index) => (
                <span key={index} className="flex-1 rounded-t bg-blue-200/80" style={{ height: `${height}%` }} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

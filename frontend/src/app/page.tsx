import Link from "next/link";
import { Button } from "@/shared/ui/button";
import { uz } from "@/messages/uz";

export default function HomePage() {
  return (
    <section className="mx-auto grid min-h-[calc(100vh-9rem)] max-w-7xl items-center px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16 lg:px-8">
      <div className="max-w-2xl">
        <p className="mb-5 inline-flex rounded-full border border-blue-100 bg-white px-4 py-2 text-sm font-semibold text-brand shadow-sm">
          {uz.home.eyebrow}
        </p>
        <h1 className="font-[var(--font-outfit)] text-4xl font-bold leading-tight tracking-tight text-ink sm:text-5xl lg:text-6xl">
          {uz.home.title}
        </h1>
        <p className="mt-6 max-w-xl text-lg leading-8 text-muted">{uz.home.description}</p>
        <div className="mt-9 flex flex-wrap items-center gap-4">
          <Button asChild size="lg">
            <Link href="/dashboard/">{uz.home.primaryAction}</Link>
          </Button>
          <span className="text-sm font-medium text-muted">{uz.home.phaseLabel}</span>
        </div>
      </div>
      <div aria-hidden="true" className="mt-14 hidden lg:block">
        <div className="relative mx-auto aspect-square max-w-[420px] rounded-[2rem] bg-gradient-to-br from-slate-900 via-blue-900 to-blue-600 p-8 shadow-soft">
          <div className="absolute -right-5 -top-5 size-24 rounded-3xl bg-violet-400/80 blur-2xl" />
          <div className="relative flex h-full flex-col justify-between rounded-3xl border border-white/20 bg-white/10 p-7 backdrop-blur-sm">
            <div className="space-y-3">
              <div className="h-3 w-28 rounded-full bg-white/80" />
              <div className="h-3 w-44 rounded-full bg-white/30" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              {["NPV", "ROI", "Daromad", "Muddat"].map((item, index) => (
                <div key={item} className="rounded-2xl border border-white/15 bg-white/10 p-4">
                  <div className="text-xs text-blue-100">{item}</div>
                  <div className="mt-3 h-3 w-16 rounded-full bg-white/70" />
                  <div className={`mt-4 h-1.5 rounded-full ${index % 2 ? "bg-emerald-300" : "bg-violet-300"}`} />
                </div>
              ))}
            </div>
            <div className="h-24 rounded-2xl border border-white/15 bg-white/10 p-4">
              <div className="h-2 w-24 rounded-full bg-white/60" />
              <div className="mt-5 flex h-10 items-end gap-2">
                {[34, 58, 43, 75, 61, 90, 70].map((height, index) => (
                  <span key={index} className="flex-1 rounded-t bg-blue-200/80" style={{ height: `${height}%` }} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

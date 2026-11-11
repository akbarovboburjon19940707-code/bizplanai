import Link from "next/link";
import { uz } from "@/messages/uz";
import type { components } from "@/shared/api/schema";
import { cn } from "@/shared/lib/cn";
import { formatDate } from "@/shared/lib/format";

type Subscription = components["schemas"]["SubscriptionOut"];
const t = uz.account.subscription;

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number }) {
  const ratio = limit > 0 ? Math.min(used / limit, 1) : 1;
  const tone = ratio >= 1 ? "bg-red-500" : ratio >= 0.8 ? "bg-amber-500" : "bg-brand";
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm">
        <span className="font-medium text-ink">{label}</span>
        <span className="tabular-nums text-muted">{t.used(used, limit)}</span>
      </div>
      <div
        className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={limit}
        aria-valuenow={Math.min(used, limit)}
      >
        <div className={cn("h-full rounded-full transition-all", tone)} style={{ width: `${ratio * 100}%` }} />
      </div>
    </div>
  );
}

export function SubscriptionCard({ subscription: s, credits }: { subscription: Subscription; credits: number }) {
  const noDocs = s.monthly_limit <= 0; // bepul tarif: hujjat faqat kredit (bitta reja) yoki pullik tarif bilan
  const exhausted = !noDocs && (s.daily_used >= s.daily_limit || s.monthly_used >= s.monthly_limit) && credits <= 0;
  return (
    <section className="rounded-card border border-border bg-white p-5 shadow-soft sm:p-6" aria-labelledby="sub-title">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h2 id="sub-title" className="text-base font-bold text-ink">{t.title}</h2>
        <span
          className={cn(
            "rounded-full px-3 py-1 text-xs font-semibold",
            s.status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600",
          )}
        >
          {s.tariff_name}
          {s.status === "active" && s.ends_at ? ` · ${t.activeUntil(formatDate(s.ends_at))}` : ""}
        </span>
      </div>
      {noDocs ? (
        <p className="mt-4 rounded-control bg-blue-50 px-3 py-2.5 text-sm text-blue-900">
          {t.freeNoDocs}{" "}
          <Link href="/tariflar/" className="font-semibold underline">{t.toTariffs}</Link>
        </p>
      ) : (
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <UsageBar label={t.daily} used={s.daily_used} limit={s.daily_limit} />
          <UsageBar label={t.monthly} used={s.monthly_used} limit={s.monthly_limit} />
        </div>
      )}
      <dl className="mt-5 grid gap-2 text-sm sm:grid-cols-2">
        <div className="flex justify-between gap-2 rounded-control bg-canvas px-3 py-2">
          <dt className="text-muted">{t.ai}</dt>
          <dd className={cn("font-semibold", s.ai_enabled ? "text-emerald-700" : "text-muted")}>
            {s.ai_enabled ? t.aiOn : t.aiOff}
          </dd>
        </div>
        <div className="flex justify-between gap-2 rounded-control bg-canvas px-3 py-2">
          <dt className="text-muted">{t.credits}</dt>
          <dd className="font-semibold tabular-nums text-ink">{credits}</dd>
        </div>
      </dl>
      {exhausted ? <p className="mt-4 text-sm font-medium text-red-600">{t.exhausted}</p> : null}
    </section>
  );
}

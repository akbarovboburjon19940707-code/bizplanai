"use client";

import Link from "next/link";
import { uz } from "@/messages/uz";
import { useApi } from "@/shared/api/use-api";
import { cn } from "@/shared/lib/cn";
import { formatNumber } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import { LoadError } from "./admin-shell";

const t = uz.admin.stats;
type StatKey = Exclude<keyof typeof t, "reviewCta">;
const ORDER: StatKey[] = [
  "payments_reviewing", "revenue_som", "active_subscriptions", "users_total",
  "users_24h", "plans_total", "plans_24h", "plans_failed_24h",
];

export function StatsView() {
  const stats = useApi<Record<StatKey, number>>("/v1/admin/stats");
  if (stats.error) return <LoadError message={stats.error.message} onRetry={stats.reload} />;
  const data = stats.data;
  const reviewing = data?.payments_reviewing ?? 0;
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {ORDER.map((key) => (
          <div
            key={key}
            className={cn(
              "rounded-card border bg-white p-4 shadow-soft",
              key === "payments_reviewing" && reviewing > 0 ? "border-amber-300" : "border-border",
              key === "plans_failed_24h" && (data?.[key] ?? 0) > 0 && "border-red-200",
            )}
          >
            <p className="text-xs font-medium text-muted">{t[key]}</p>
            {data ? (
              <p className="mt-2 text-2xl font-bold tabular-nums text-ink">{formatNumber(data[key])}</p>
            ) : (
              <div className="mt-3 h-7 w-20 animate-pulse rounded bg-slate-100" />
            )}
          </div>
        ))}
      </div>
      {reviewing > 0 ? (
        <Button asChild className="self-start"><Link href="/admin/tolovlar/">{t.reviewCta} ({reviewing})</Link></Button>
      ) : null}
    </div>
  );
}

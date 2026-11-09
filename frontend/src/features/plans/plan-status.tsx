"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/features/auth/auth-context";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { formatSom } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import type { PlanOut } from "./schema";

const t = uz.plans.plan;

/** /reja?id=... : holatni 2 soniyada so'raydi, tayyor bo'lsa Word va Excel yuklash. */
export function PlanStatus() {
  const id = useSearchParams().get("id");
  const { status: auth } = useAuth();
  const [plan, setPlan] = useState<PlanOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || auth !== "authenticated") return;
    let stop = false;
    let timer: number | undefined;
    const tick = async () => {
      try {
        const p = await apiRequest<PlanOut>(`/v1/plans/${encodeURIComponent(id)}`);
        if (stop) return;
        setPlan(p);
        if (p.status === "queued" || p.status === "running") timer = window.setTimeout(tick, 2000);
      } catch (e) {
        if (!stop) setError(e instanceof ApiError ? e.message : t.missing);
      }
    };
    void tick();
    return () => {
      stop = true;
      window.clearTimeout(timer);
    };
  }, [id, auth]);

  const download = async (format: "docx" | "xlsx") => {
    try {
      const { url } = await apiRequest<{ url: string }>(`/v1/plans/${encodeURIComponent(id ?? "")}/download?format=${format}`);
      window.location.href = url;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t.missing);
    }
  };

  const npv = typeof plan?.indicators?.npv === "number" ? plan.indicators.npv : null;

  return (
    <section className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <div className="rounded-card border border-border bg-white p-6 shadow-soft">
        <h1 className="font-[var(--font-outfit)] text-2xl font-bold text-ink">{plan?.title ?? t.title}</h1>
        {!id || error ? (
          <p className="mt-4 text-sm text-red-600">{error ?? t.missing}</p>
        ) : !plan ? (
          <div className="mt-4 h-5 w-40 animate-pulse rounded bg-slate-200" />
        ) : (
          <div className="mt-4 flex flex-col gap-4" aria-live="polite">
            <p className="text-sm font-semibold">
              {plan.status === "failed" ? <span className="text-red-600">{t.failed}</span> : t[plan.status as "queued" | "running" | "done"]}
            </p>
            {plan.status === "queued" || plan.status === "running" ? (
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full w-1/2 animate-pulse rounded-full bg-brand" />
              </div>
            ) : null}
            {plan.status === "done" ? (
              <>
                {npv !== null ? <p className="text-sm text-muted">NPV: {formatSom(npv)}</p> : null}
                <div className="flex flex-wrap gap-3">
                  <Button onClick={() => void download("docx")}>{t.word}</Button>
                  <Button variant="outline" onClick={() => void download("xlsx")}>
                    {t.excel}
                  </Button>
                </div>
              </>
            ) : null}
          </div>
        )}
        <Link href="/dashboard/" className="mt-6 inline-block text-sm font-semibold text-brand hover:underline">
          {t.newPlan}
        </Link>
      </div>
    </section>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { useWatch, type Control } from "react-hook-form";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { planFormSchema, toPlanInput, type PlanFormValues, type PreviewOut } from "./schema";

export type PreviewState =
  | { status: "incomplete" }
  | { status: "loading"; data: PreviewOut | null }
  | { status: "ready"; data: PreviewOut }
  | { status: "error"; message: string; data: PreviewOut | null };

/** Forma o'zgarganda 500 ms kutib POST /v1/plans/preview; eski so'rov bekor qilinadi. */
export function usePlanPreview(control: Control<PlanFormValues>): PreviewState {
  const values = useWatch({ control }) as PlanFormValues;
  const parsed = useMemo(() => planFormSchema.safeParse(values), [values]);
  const key = parsed.success ? JSON.stringify(toPlanInput(parsed.data)) : null;
  const [state, setState] = useState<PreviewState>({ status: "incomplete" });

  useEffect(() => {
    if (!key) {
      setState((s) => (s.status === "incomplete" ? s : { status: "incomplete" }));
      return;
    }
    const controller = new AbortController();
    setState((s) => ({ status: "loading", data: "data" in s ? s.data : null }));
    const timer = window.setTimeout(async () => {
      try {
        const data = await apiRequest<PreviewOut>("/v1/plans/preview", {
          method: "POST",
          body: key,
          signal: controller.signal,
        });
        setState({ status: "ready", data });
      } catch (error) {
        if (controller.signal.aborted) return;
        const message = error instanceof ApiError ? error.message : "So‘rovni bajarib bo‘lmadi";
        setState((s) => ({ status: "error", message, data: "data" in s ? s.data : null }));
      }
    }, 500);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [key]);

  return state;
}

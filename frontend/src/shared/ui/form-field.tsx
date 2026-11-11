import type { ReactNode } from "react";
import { cn } from "@/shared/lib/cn";

export const inputClass =
  "w-full rounded-control border border-border bg-white px-3 py-2.5 text-sm text-ink shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand focus:ring-2 focus:ring-blue-100 disabled:bg-slate-50 disabled:text-muted aria-[invalid=true]:border-red-400";

/** Yorliq + maydon + xato/izoh. `id` maydonning id si bilan bir xil bo'lsin (label va aria uchun). */
export function FormField({
  id,
  label,
  hint,
  error,
  children,
  className,
}: {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} role="alert" className="text-xs font-medium text-red-600">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-xs text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

/** Maydon uchun aria atributlari (xato bo'lsa xatoga, bo'lmasa izohga bog'lanadi). */
export function fieldAria(id: string, error?: string, hint?: string) {
  return {
    "aria-invalid": error ? true : undefined,
    "aria-describedby": error ? `${id}-error` : hint ? `${id}-hint` : undefined,
  } as const;
}

/** Forma darajasidagi xabar (masalan, "parol noto'g'ri"). */
export function FormAlert({ tone = "error", children }: { tone?: "error" | "success" | "info"; children: ReactNode }) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "rounded-control border px-3 py-2.5 text-sm",
        tone === "error" && "border-red-200 bg-red-50 text-red-700",
        tone === "success" && "border-emerald-200 bg-emerald-50 text-emerald-800",
        tone === "info" && "border-blue-100 bg-blue-50 text-blue-900",
      )}
    >
      {children}
    </div>
  );
}

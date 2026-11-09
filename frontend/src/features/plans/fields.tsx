"use client";

import { useId, useState, type ReactNode } from "react";
import { Controller, useFormContext, type FieldPath } from "react-hook-form";
import { cn } from "@/shared/lib/cn";
import { formatNumber, parseNumber } from "@/shared/lib/format";
import type { PlanFormValues } from "./schema";

type Name = FieldPath<PlanFormValues>;

const inputClass =
  "w-full rounded-control border border-border bg-white px-3 py-2.5 text-sm text-ink shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand focus:ring-2 focus:ring-blue-100 aria-[invalid=true]:border-red-400";

function getError(errors: Record<string, unknown>, name: string): string | undefined {
  let cur: unknown = errors;
  for (const part of name.split(".")) {
    if (!cur || typeof cur !== "object") return undefined;
    cur = (cur as Record<string, unknown>)[part];
  }
  const msg = (cur as { message?: unknown } | undefined)?.message;
  return typeof msg === "string" ? msg : undefined;
}

export function Field({
  label,
  hint,
  error,
  id,
  children,
  className,
}: {
  label: string;
  hint?: string;
  error?: string;
  id: string;
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
        <p id={`${id}-error`} className="text-xs font-medium text-red-600">
          {error}
        </p>
      ) : hint ? (
        <p className="text-xs text-muted">{hint}</p>
      ) : null}
    </div>
  );
}

export function TextField({ name, label, placeholder, hint, className }: {
  name: Name; label: string; placeholder?: string; hint?: string; className?: string;
}) {
  const id = useId();
  const { register, formState } = useFormContext<PlanFormValues>();
  const error = getError(formState.errors, name);
  return (
    <Field id={id} label={label} hint={hint} error={error} className={className}>
      <input
        id={id}
        className={inputClass}
        placeholder={placeholder}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        {...register(name)}
      />
    </Field>
  );
}

/** Raqam maydoni: ekranda "1 000 000", formada number | undefined. */
export function NumberField({ name, label, hint, placeholder, integer, className }: {
  name: Name; label: string; hint?: string; placeholder?: string; integer?: boolean; className?: string;
}) {
  const id = useId();
  const { control, formState } = useFormContext<PlanFormValues>();
  const error = getError(formState.errors, name);
  return (
    <Field id={id} label={label} hint={hint} error={error} className={className}>
      <Controller
        control={control}
        name={name}
        render={({ field }) => (
          <NumberInput
            id={id}
            value={typeof field.value === "number" ? field.value : undefined}
            onChange={(v) => field.onChange(integer && v !== undefined ? Math.round(v) : v)}
            onBlur={field.onBlur}
            placeholder={placeholder}
            invalid={Boolean(error)}
          />
        )}
      />
    </Field>
  );
}

export function NumberInput({ id, value, onChange, onBlur, placeholder, invalid, className }: {
  id?: string; value: number | undefined; onChange: (v: number | undefined) => void; onBlur?: () => void;
  placeholder?: string; invalid?: boolean; className?: string;
}) {
  const [draft, setDraft] = useState<string | null>(null);
  return (
    <input
      id={id}
      inputMode="decimal"
      className={cn(inputClass, "text-right tabular-nums", className)}
      placeholder={placeholder}
      aria-invalid={invalid ? true : undefined}
      value={draft ?? formatNumber(value)}
      onFocus={() => setDraft(value === undefined ? "" : String(value))}
      onChange={(e) => {
        setDraft(e.target.value);
        onChange(parseNumber(e.target.value));
      }}
      onBlur={() => {
        setDraft(null);
        onBlur?.();
      }}
    />
  );
}

export function ChoiceField<T extends string>({ name, label, options, columns = 2 }: {
  name: Name; label: string; options: { value: T; label: string }[]; columns?: 2 | 4;
}) {
  const { register, watch } = useFormContext<PlanFormValues>();
  const current = watch(name);
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1.5 text-sm font-medium text-ink">{label}</legend>
      <div className={cn("grid gap-2", columns === 4 ? "grid-cols-2 lg:grid-cols-4" : "grid-cols-1 sm:grid-cols-2")}>
        {options.map((o) => (
          <label
            key={o.value}
            className={cn(
              "flex cursor-pointer items-center gap-2 rounded-control border px-3 py-2.5 text-sm transition focus-within:ring-2 focus-within:ring-blue-100",
              current === o.value ? "border-brand bg-blue-50 font-semibold text-brand-dark" : "border-border bg-white text-ink hover:bg-canvas",
            )}
          >
            <input type="radio" value={o.value} className="sr-only" {...register(name)} />
            {o.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <section className="rounded-card border border-border bg-white p-4 shadow-sm sm:p-6">
      <h2 className="font-[var(--font-outfit)] text-lg font-bold text-ink">{title}</h2>
      {hint ? <p className="mt-1 text-sm text-muted">{hint}</p> : null}
      <div className="mt-4 grid gap-4 sm:grid-cols-2">{children}</div>
    </section>
  );
}

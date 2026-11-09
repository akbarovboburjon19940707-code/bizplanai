"use client";

import { Controller, useFormContext } from "react-hook-form";
import { uz } from "@/messages/uz";
import { Button } from "@/shared/ui/button";
import { NumberField, NumberInput } from "./fields";
import { IndicatorCards, PreviewTables } from "./preview-panel";
import { DEFAULT_CAPACITY, DEFAULT_DISCOUNT, type PlanFormValues } from "./schema";
import type { PreviewState } from "./use-preview";

const t = uz.plans.result;

export function StepResult({ preview }: { preview: PreviewState }) {
  const { control, register, setValue } = useFormContext<PlanFormValues>();
  return (
    <div className="flex flex-col gap-4">
      <section className="rounded-card border border-border bg-white p-4 shadow-sm sm:p-6 lg:hidden">
        <h2 className="mb-3 font-[var(--font-outfit)] text-lg font-bold text-ink">{t.indicators}</h2>
        <IndicatorCards state={preview} />
      </section>

      <details className="rounded-card border border-border bg-white p-4 shadow-sm sm:p-6">
        <summary className="cursor-pointer font-[var(--font-outfit)] text-lg font-bold text-ink">{t.advanced}</summary>
        <fieldset className="mt-4">
          <legend className="text-sm font-medium text-ink">{t.quvvat}</legend>
          <div className="mt-2 grid grid-cols-5 gap-2 sm:grid-cols-10">
            {DEFAULT_CAPACITY.map((_, i) => (
              <Controller
                key={i}
                control={control}
                name={`quvvat.${i}`}
                render={({ field }) => (
                  <label className="flex flex-col items-center gap-1 text-xs text-muted">
                    {i + 1}
                    <NumberInput
                      value={field.value}
                      onChange={(v) => field.onChange(v ?? 0)}
                      onBlur={field.onBlur}
                      className="px-1 text-center"
                    />
                  </label>
                )}
              />
            ))}
          </div>
        </fieldset>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <NumberField name="diskont" label={t.diskont} />
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="mt-3"
          onClick={() => {
            setValue("quvvat", [...DEFAULT_CAPACITY], { shouldDirty: true });
            setValue("diskont", DEFAULT_DISCOUNT, { shouldDirty: true });
          }}
        >
          {t.reset}
        </Button>
      </details>

      <PreviewTables state={preview} />

      <label className="flex items-center gap-3 rounded-card border border-border bg-white p-4 text-sm shadow-sm">
        <input type="checkbox" className="size-4 accent-[#2563eb]" {...register("use_ai")} />
        {t.useAi}
      </label>
    </div>
  );
}

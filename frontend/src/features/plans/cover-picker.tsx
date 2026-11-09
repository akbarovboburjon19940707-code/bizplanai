"use client";

import { useEffect, useId, useState } from "react";
import { useFormContext } from "react-hook-form";
import { uz } from "@/messages/uz";
import { ChoiceField } from "./fields";
import type { PlanFormValues } from "./schema";

const t = uz.plans.cover;
export const MAX_COVER_BYTES = 5 * 1024 * 1024;
const TYPES = ["image/jpeg", "image/png"];

/** Muqova rasmi: avtomatik, o'zi yuklaydi yoki rasmsiz. Fayl faqat xotirada (sessionStorage'ga yozilmaydi). */
export function CoverPicker({ file, onFile }: { file: File | null; onFile: (f: File | null) => void }) {
  const { watch } = useFormContext<PlanFormValues>();
  const mode = watch("rasm_turi");
  const id = useId();
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (!file) return setPreview(null);
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  return (
    <section className="rounded-card border border-border bg-white p-4 shadow-sm sm:p-6">
      <h2 className="font-[var(--font-outfit)] text-lg font-bold text-ink">{t.title}</h2>
      <p className="mt-1 text-sm text-muted">{t.hint}</p>
      <div className="mt-4">
        <ChoiceField
          name="rasm_turi"
          label={t.title}
          options={[
            { value: "avto", label: t.avto },
            { value: "yuklash", label: t.yuklash },
            { value: "yoq", label: t.yoq },
          ]}
        />
      </div>
      {mode === "yuklash" ? (
        <div className="mt-4 flex flex-col gap-2">
          <span className="text-sm font-medium text-ink">{t.choose}</span>
          {/* Brauzerning o'z tugmasi tizim tilida chiqadi, shuning uchun yashirin input + o'zbekcha tugma */}
          <div className="flex flex-wrap items-center gap-3">
            <input
              id={id}
              type="file"
              accept="image/jpeg,image/png"
              aria-label={t.choose}
              aria-invalid={error ? true : undefined}
              className="peer sr-only"
              onChange={(e) => {
                const f = e.target.files?.[0] ?? null;
                setError(null);
                if (f && !TYPES.includes(f.type)) {
                  setError(t.badType);
                  e.target.value = "";
                  return onFile(null);
                }
                if (f && f.size > MAX_COVER_BYTES) {
                  setError(t.tooBig);
                  e.target.value = "";
                  return onFile(null);
                }
                onFile(f);
              }}
            />
            <label
              htmlFor={id}
              className="cursor-pointer rounded-control bg-blue-50 px-4 py-2 text-sm font-semibold text-brand-dark hover:bg-blue-100 peer-focus-visible:ring-2 peer-focus-visible:ring-brand"
            >
              {t.button}
            </label>
            <span className="text-sm text-muted">{file?.name ?? t.noFile}</span>
          </div>
          {error ? <p className="text-xs font-medium text-red-600">{error}</p> : <p className="text-xs text-muted">{t.lostHint}</p>}
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element -- static export: next/image optimizatsiyasiz
            <img src={preview} alt={t.preview} className="mt-2 max-h-48 w-auto rounded-control border border-border object-contain" />
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

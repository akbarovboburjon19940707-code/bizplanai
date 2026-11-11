"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FormProvider, useForm, type FieldPath } from "react-hook-form";
import { useAuth } from "@/features/auth/auth-context";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import type { components } from "@/shared/api/schema";
import { useApi } from "@/shared/api/use-api";
import { Button } from "@/shared/ui/button";
import { Paywall } from "./paywall";
import { IndicatorCards } from "./preview-panel";
import { defaultValues, planFormSchema, toPlanInput, type PlanFormValues, type PlanOut } from "./schema";
import { StepProducts } from "./step-products";
import { StepResult } from "./step-result";
import { StepFinance, StepProject, StepStaff } from "./steps-basic";
import { usePlanPreview } from "./use-preview";

const t = uz.plans;
const DRAFT_KEY = "bp_plan_draft"; // faqat forma ma'lumoti, token emas
// Shaxsiy identifikatorlar qoralamaga yozilmaydi (sahifa yangilansa qayta kiritiladi)
const DRAFT_EXCLUDE = ["jshshir", "stir"] as const;

// Har bosqichda "Keyingi" bosilganda tekshiriladigan maydonlar
const STEP_FIELDS: FieldPath<PlanFormValues>[][] = [
  ["faoliyat_turi", "loyiha_nomi", "stir", "jshshir", "soliq_turi"],
  ["loyiha_qiymati", "oz_mablag", "kredit", "foiz", "muddat", "imtiyoz"],
  ["mahsulotlar", "tannarx_ulushi"],
  ["direktor", "xodim", "yangi_xodim"],
  [],
];

function loadDraft(): PlanFormValues {
  try {
    const raw = window.sessionStorage.getItem(DRAFT_KEY);
    if (raw) return { ...defaultValues, ...(JSON.parse(raw) as Partial<PlanFormValues>) };
  } catch {
    // buzilgan qoralama e'tiborsiz qoldiriladi
  }
  return defaultValues;
}

export function PlanWizard() {
  const router = useRouter();
  const { status } = useAuth();
  // Hujjat yaratish imkoni: kredit yoki tarif limiti. Bo'lmasa (bepul tarif) "Yaratish" o'rnida to'lov taklifi.
  const me = useApi<components["schemas"]["MeOut"]>(status === "authenticated" ? "/v1/me" : null);
  const [paymentRequired, setPaymentRequired] = useState(false);
  const sub = me.data?.subscription;
  const canCreate = !me.data || me.data.user.plan_credits > 0
    || (!!sub && sub.daily_used < sub.daily_limit && sub.monthly_used < sub.monthly_limit);
  const showPaywall = status === "authenticated" && (paymentRequired || !canCreate);
  const [step, setStep] = useState(0);
  const [submitError, setSubmitError] = useState<{ message: string; quota?: boolean } | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null); // faqat xotirada
  const form = useForm<PlanFormValues>({ resolver: zodResolver(planFormSchema), defaultValues, mode: "onTouched" });
  const preview = usePlanPreview(form.control);

  useEffect(() => {
    form.reset(loadDraft());
  }, [form]);

  useEffect(() => {
    const sub = form.watch((values) => {
      try {
        const draft: Record<string, unknown> = { ...values };
        for (const key of DRAFT_EXCLUDE) delete draft[key];
        window.sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
      } catch {
        // xotira to'lgan yoki o'chirilgan
      }
    });
    return () => sub.unsubscribe();
  }, [form]);

  const goNext = async () => {
    if (await form.trigger(STEP_FIELDS[step])) setStep((s) => Math.min(s + 1, 4));
  };

  const onSubmit = form.handleSubmit(async (values) => {
    setSubmitError(null);
    try {
      const input = toPlanInput(values);
      if (values.rasm_turi === "yuklash" && coverFile) {
        const body = new FormData();
        body.append("file", coverFile);
        const { image_id } = await apiRequest<{ image_id: string }>("/v1/plans/images", { method: "POST", body });
        input.rasm_id = image_id;
      }
      const plan = await apiRequest<PlanOut>("/v1/plans", {
        method: "POST",
        body: JSON.stringify({ input, use_ai: values.use_ai }),
      });
      window.sessionStorage.removeItem(DRAFT_KEY);
      router.push(`/reja/?id=${encodeURIComponent(plan.id)}`);
    } catch (error) {
      if (!(error instanceof ApiError)) return setSubmitError({ message: "So‘rovni bajarib bo‘lmadi" });
      if (error.code === "quota_exceeded") {
        const reason = (error.details as { reason?: string } | undefined)?.reason;
        if (reason === "payment_required") return setPaymentRequired(true);
        return setSubmitError({ message: error.message, quota: true });
      }
      if (error.code === "validation_error" && Array.isArray(error.details)) {
        for (const d of error.details as { field?: string; message?: string }[]) {
          if (d.field) form.setError(d.field.replace(/^input\./, "") as FieldPath<PlanFormValues>, { message: d.message });
        }
      }
      setSubmitError({ message: error.message });
    }
  });

  const StepView = [null, StepFinance, StepProducts, StepStaff][step];

  return (
    <FormProvider {...form}>
      <form
        onSubmit={(e) => {
          // Faqat 5-bosqichdagi "Yaratish" yuboradi; oldingi bosqichlarda Enter = "Keyingi"
          if (step < 4) {
            e.preventDefault();
            void goNext();
            return;
          }
          void onSubmit(e);
        }}
        noValidate className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_20rem] lg:px-8">
        <div className="min-w-0">
          <h1 className="font-[var(--font-outfit)] text-2xl font-bold text-ink sm:text-3xl">{t.title}</h1>
          <p className="mt-1 text-sm text-muted">{t.subtitle}</p>
          <nav aria-label={t.title} className="mt-5 overflow-x-auto">
            <ol className="flex min-w-max gap-2">
              {t.steps.map((label, i) => (
                <li key={label}>
                  <button
                    type="button"
                    onClick={() => (i < step ? setStep(i) : undefined)}
                    aria-current={i === step ? "step" : undefined}
                    className={`rounded-full px-3 py-1.5 text-xs font-semibold sm:text-sm ${
                      i === step ? "bg-brand text-white" : i < step ? "bg-blue-50 text-brand-dark" : "bg-white text-muted"
                    }`}
                  >
                    {i + 1}. {label}
                  </button>
                </li>
              ))}
            </ol>
          </nav>
          <div className="mt-5">
            {step === 0 ? (
              <StepProject coverFile={coverFile} onCoverFile={setCoverFile} />
            ) : step === 4 ? (
              <StepResult preview={preview} />
            ) : StepView ? (
              <StepView />
            ) : null}
          </div>

          {submitError ? (
            <p role="alert" className="mt-4 rounded-control bg-red-50 p-3 text-sm text-red-700">
              {submitError.message}{" "}
              {submitError.quota ? (
                <Link href="/tariflar/" className="font-semibold underline">
                  {t.result.tariffs}
                </Link>
              ) : null}
            </p>
          ) : null}

          {step === 4 && showPaywall ? <Paywall /> : null}

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
            <Button type="button" variant="outline" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>
              {t.back}
            </Button>
            {step < 4 ? (
              <Button key="next" type="button" onClick={goNext}>
                {t.next}
              </Button>
            ) : status === "authenticated" && showPaywall ? null : status === "authenticated" ? (
              // key: React yangi DOM tugma yaratadi, "Keyingi" bosilishi "Yaratish" bo'lib yuborilmaydi
              <Button key="create" type="submit" size="lg" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? t.result.creating : t.result.create}
              </Button>
            ) : (
              <div className="flex flex-col items-end gap-2 text-right">
                <p className="max-w-sm text-sm text-muted">{t.result.loginRequired}</p>
                <Button asChild size="lg">
                  <Link href="/kirish/?next=/dashboard/">{t.result.login}</Link>
                </Button>
              </div>
            )}
          </div>
        </div>

        <aside className="hidden lg:block">
          <div className="sticky top-24 rounded-card border border-border bg-white p-4 shadow-soft">
            <h2 className="mb-3 font-[var(--font-outfit)] text-base font-bold text-ink">{t.result.indicators}</h2>
            <IndicatorCards state={preview} />
          </div>
        </aside>
      </form>
    </FormProvider>
  );
}

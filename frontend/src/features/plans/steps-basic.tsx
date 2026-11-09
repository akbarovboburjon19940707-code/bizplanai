"use client";

import { useFormContext } from "react-hook-form";
import { uz } from "@/messages/uz";
import { ChoiceField, NumberField, Section, TextField } from "./fields";
import { ACTIVITIES, type PlanFormValues } from "./schema";

const t = uz.plans;

export function StepProject() {
  return (
    <div className="flex flex-col gap-4">
      <section className="rounded-card border border-border bg-white p-4 shadow-sm sm:p-6">
        <ChoiceField
          name="faoliyat_turi"
          label={t.activity.label}
          columns={4}
          options={ACTIVITIES.map((a) => ({ value: a, label: t.activity[a] }))}
        />
        <div className="mt-4">
          <TextField name="loyiha_nomi" label={t.project.loyiha_nomi} placeholder={t.project.loyiha_nomi_ph} />
        </div>
      </section>
      <Section title={t.steps[0]}>
        <TextField name="tashabbuskor" label={t.project.tashabbuskor} placeholder={t.project.tashabbuskor_ph} />
        <TextField name="fio" label={t.project.fio} />
        <TextField name="mulk" label={t.project.mulk} placeholder="MChJ, YaTT, FX" />
        <TextField name="stir" label={t.project.stir} placeholder={t.project.stir_ph} />
        <TextField name="faoliyat_turi_text" label={t.project.faoliyat_turi_text} />
        <TextField name="bank" label={t.project.bank} />
        <TextField name="manzil" label={t.project.manzil} placeholder={t.project.manzil_ph} className="sm:col-span-2" />
        <TextField name="ro_sana" label={t.project.ro_sana} placeholder="KK.OO.YYYY" />
        <div className="sm:col-span-2">
          <ChoiceField
            name="soliq_turi"
            label={t.project.soliq_turi}
            options={[
              { value: "ytt", label: t.project.ytt },
              { value: "mchj", label: t.project.mchj },
            ]}
          />
        </div>
      </Section>
    </div>
  );
}

export function StepFinance() {
  const { watch } = useFormContext<PlanFormValues>();
  const [lq, oz, kredit] = watch(["loyiha_qiymati", "oz_mablag", "kredit"]);
  const mismatch = typeof lq === "number" && (oz || kredit) && Math.abs(lq - (oz ?? 0) - (kredit ?? 0)) > 1;
  return (
    <div className="flex flex-col gap-4">
      <Section title={t.steps[1]} hint={t.finance.feeHint}>
        <NumberField name="loyiha_qiymati" label={t.finance.loyiha_qiymati} />
        <NumberField name="oz_mablag" label={t.finance.oz_mablag} />
        <NumberField name="kredit" label={t.finance.kredit} />
        <NumberField name="aylanma_kapital" label={t.finance.aylanma_kapital} />
        <NumberField name="sugurta" label={t.finance.sugurta} />
        {mismatch ? (
          <p role="status" className="rounded-control bg-amber-50 px-3 py-2 text-sm text-amber-800 sm:col-span-2">
            {t.finance.sumMismatch}
          </p>
        ) : null}
      </Section>
      <Section title={t.finance.kredit}>
        <NumberField name="foiz" label={t.finance.foiz} />
        <NumberField name="muddat" label={t.finance.muddat} integer />
        <NumberField name="imtiyoz" label={t.finance.imtiyoz} integer />
        <div className="sm:col-span-2">
          <ChoiceField
            name="kredit_turi"
            label={t.finance.kredit_turi}
            options={[
              { value: "differensial", label: t.finance.differensial },
              { value: "annuitet", label: t.finance.annuitet },
            ]}
          />
        </div>
      </Section>
    </div>
  );
}

export function StepStaff() {
  return (
    <Section title={t.steps[3]} hint={t.staff.socialHint}>
      <NumberField name="direktor" label={t.staff.direktor} integer />
      <NumberField name="rahbar_oylik" label={t.staff.rahbar_oylik} />
      <NumberField name="xodim" label={t.staff.xodim} integer />
      <NumberField name="ishchi_oylik" label={t.staff.ishchi_oylik} />
      <NumberField name="yangi_xodim" label={t.staff.yangi_xodim} integer />
      <NumberField name="yangi_ishchi_oylik" label={t.staff.yangi_ishchi_oylik} />
    </Section>
  );
}

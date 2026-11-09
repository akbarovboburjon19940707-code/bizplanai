"use client";

import { useFieldArray, useFormContext } from "react-hook-form";
import { uz } from "@/messages/uz";
import { Button } from "@/shared/ui/button";
import { NumberField, Section, TextField } from "./fields";
import { DEFAULT_COGS_PCT, type PlanFormValues } from "./schema";

const t = uz.plans;

// Faoliyat turiga mos qo'shimcha xarajat maydonlari
const COSTS_BY_ACTIVITY = {
  ishlab_chiqarish: ["joy_ijarasi", "transport_xarajat"],
  qishloq_xojaligi: ["urug_yem_narx", "texnika_xarajat", "yer_ijarasi", "transport_xarajat"],
  savdo: ["dokon_ijarasi", "transport_xarajat"],
  xizmat: ["joy_ijarasi", "transport_xarajat"],
} as const;

export function StepProducts() {
  const { control, watch } = useFormContext<PlanFormValues>();
  const { fields, append, remove } = useFieldArray({ control, name: "mahsulotlar" });
  const faoliyat = watch("faoliyat_turi");

  return (
    <div className="flex flex-col gap-4">
      <section className="rounded-card border border-border bg-white p-4 shadow-sm sm:p-6">
        <h2 className="font-[var(--font-outfit)] text-lg font-bold text-ink">{t.products.title}</h2>
        <p className="mt-1 text-sm text-muted">{t.products.hint}</p>
        <ol className="mt-4 flex flex-col gap-4">
          {fields.map((f, i) => (
            <li key={f.id} className="rounded-control border border-border bg-canvas/50 p-3 sm:p-4">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-sm font-semibold text-ink">#{i + 1}</span>
                {fields.length > 1 ? (
                  <Button type="button" variant="ghost" size="sm" onClick={() => remove(i)}>
                    {t.products.remove}
                  </Button>
                ) : null}
              </div>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <TextField name={`mahsulotlar.${i}.nomi`} label={t.products.nomi} className="sm:col-span-2 lg:col-span-1" />
                <NumberField name={`mahsulotlar.${i}.hajm`} label={t.products.hajm} />
                <TextField name={`mahsulotlar.${i}.olchov`} label={t.products.olchov} placeholder="dona, kg, tonna" />
                <NumberField name={`mahsulotlar.${i}.narx`} label={t.products.narx} />
                <NumberField
                  name={`mahsulotlar.${i}.xomashyo_narx`}
                  label={t.products.xomashyo_narx}
                  hint={t.products.xomashyo_hint}
                />
              </div>
            </li>
          ))}
        </ol>
        {fields.length < 6 ? (
          <Button
            type="button"
            variant="outline"
            className="mt-4"
            onClick={() => append({ nomi: "", hajm: undefined as unknown as number, narx: undefined as unknown as number, olchov: "dona" })}
          >
            + {t.products.add}
          </Button>
        ) : null}
        <div className="mt-5 max-w-sm">
          <NumberField
            name="tannarx_ulushi"
            label={t.products.tannarx_ulushi}
            hint={t.products.tannarxDefault.replace("{pct}", String(DEFAULT_COGS_PCT[faoliyat]))}
          />
        </div>
      </section>

      <Section title={t.products.costs}>
        {COSTS_BY_ACTIVITY[faoliyat].map((name) => (
          <NumberField key={name} name={name} label={t.costs[name]} />
        ))}
      </Section>

      <Section title={t.products.utilities}>
        <NumberField name="elektr" label={t.costs.elektr} />
        <NumberField name="gaz" label={t.costs.gaz} />
        <NumberField name="suv" label={t.costs.suv} />
        <NumberField name="oqava" label={t.costs.oqava} />
        <NumberField name="boshqa_kommunal" label={t.costs.boshqa_kommunal} />
      </Section>
    </div>
  );
}

import { z } from "zod";
import type { components } from "@/shared/api/schema";

export type PlanInput = components["schemas"]["PlanInput"];
export type PreviewOut = components["schemas"]["PreviewOut"];
export type PlanOut = components["schemas"]["PlanOut"];

export const ACTIVITIES = ["ishlab_chiqarish", "qishloq_xojaligi", "savdo", "xizmat"] as const;
export type Activity = (typeof ACTIVITIES)[number];

// Backend standartlari (backend/app/engine/template_model.py bilan bir xil)
export const DEFAULT_COGS_PCT: Record<Activity, number> = {
  savdo: 75,
  ishlab_chiqarish: 55,
  qishloq_xojaligi: 40,
  xizmat: 15,
};
export const DEFAULT_CAPACITY = [75, 77, 80, 82, 85, 90, 92, 95, 100, 100];

/** Loyiha davri (yil) kredit muddatidan: backend `horizon_years` bilan bir xil (36 oy -> 3, 30 oy -> 3; 1..10). */
export function horizonYears(muddat: number | null | undefined): number {
  const m = muddat && muddat > 0 ? muddat : 120;
  return Math.max(1, Math.min(10, Math.ceil(m / 12)));
}
export const DEFAULT_DISCOUNT = 14;

const money = z.number().min(0).max(1e13).optional();
const count = z.number().int().min(0).max(100_000).optional();
const text = (max: number) => z.string().max(max).optional();

export const productSchema = z.object({
  nomi: z.string().trim().min(1, "Nomini kiriting").max(200),
  hajm: z.number({ required_error: "Hajmni kiriting" }).gt(0, "Hajm musbat bo‘lsin").max(1e12),
  narx: z.number({ required_error: "Narxni kiriting" }).gt(0, "Narx musbat bo‘lsin").max(1e12),
  olchov: text(30),
  xomashyo_narx: money,
});

export const planFormSchema = z.object({
  faoliyat_turi: z.enum(ACTIVITIES),
  loyiha_nomi: z.string().trim().min(2, "Kamida 2 ta belgi").max(200),
  tashabbuskor: text(200),
  fio: text(150),
  mulk: text(50),
  stir: z
    .string()
    .regex(/^(\d{9})?$/, "STIR 9 ta raqamdan iborat")
    .optional(),
  jshshir: z
    .string()
    .regex(/^(\d{14})?$/, "JShShIR 14 ta raqamdan iborat")
    .optional(),
  faoliyat_turi_text: text(200),
  manzil: text(300),
  bank: text(150),
  soliq_turi: z.enum(["ytt", "mchj"]),
  ro_sana: text(20),

  loyiha_qiymati: z.number({ required_error: "Loyiha qiymatini kiriting" }).gt(0, "Musbat summa").max(1e13),
  oz_mablag: money,
  kredit: money,
  aylanma_kapital: money,
  sugurta: money,
  foiz: z.number().min(0).max(100).optional(),
  muddat: z.number().int().min(1).max(360).optional(),
  imtiyoz: z.number().int().min(0).max(120).optional(),
  kredit_turi: z.enum(["differensial", "annuitet"]),

  mahsulotlar: z.array(productSchema).min(1).max(6),
  tannarx_ulushi: z.number().min(0).max(100).optional(),
  urug_yem_narx: money,
  texnika_xarajat: money,
  yer_ijarasi: money,
  dokon_ijarasi: money,
  joy_ijarasi: money,
  transport_xarajat: money,
  elektr: money,
  gaz: money,
  suv: money,
  oqava: money,
  boshqa_kommunal: money,

  direktor: count,
  rahbar_oylik: money,
  xodim: count,
  ishchi_oylik: money,
  yangi_xodim: count,
  yangi_ishchi_oylik: money,

  quvvat: z.array(z.number().min(0).max(150)).length(10),
  diskont: z.number().min(0).max(100),
  use_ai: z.boolean(),
  rasm_turi: z.enum(["avto", "yuklash", "yoq"]),
});

export type PlanFormValues = z.infer<typeof planFormSchema>;

export const defaultValues: PlanFormValues = {
  faoliyat_turi: "ishlab_chiqarish",
  loyiha_nomi: "",
  soliq_turi: "ytt",
  loyiha_qiymati: undefined as unknown as number,
  kredit_turi: "differensial",
  foiz: 18,
  muddat: 120,
  imtiyoz: 24,
  mahsulotlar: [{ nomi: "", hajm: undefined as unknown as number, narx: undefined as unknown as number, olchov: "dona" }],
  direktor: 1,
  quvvat: [...DEFAULT_CAPACITY],
  diskont: DEFAULT_DISCOUNT,
  use_ai: true,
  rasm_turi: "avto",
};

const sameList = (a: number[], b: number[]) => a.length === b.length && a.every((v, i) => v === b[i]);

/** Forma qiymatlaridan API uchun PlanInput: bo‘sh maydonlar yuborilmaydi, standart sozlamalar ham. */
export function toPlanInput(values: PlanFormValues): PlanInput {
  const { quvvat, diskont, mahsulotlar, rasm_turi, ...rest } = values;
  const out: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(rest)) {
    if (key === "use_ai" || value === undefined || value === null || value === "") continue;
    out[key] = typeof value === "string" ? value.trim() : value;
  }
  out.mahsulotlar = mahsulotlar.map((p) => ({
    nomi: p.nomi.trim(),
    hajm: p.hajm,
    narx: p.narx,
    ...(p.olchov ? { olchov: p.olchov.trim() } : {}),
    ...(p.xomashyo_narx ? { xomashyo_narx: p.xomashyo_narx } : {}),
  }));
  out.mahsulot = mahsulotlar.map((p) => p.nomi.trim()).join(", ");
  if (!sameList(quvvat, DEFAULT_CAPACITY)) out.quvvat = quvvat;
  if (diskont !== DEFAULT_DISCOUNT) out.diskont = diskont;
  out.rasm_avto = rasm_turi === "avto";
  return out as PlanInput;
}

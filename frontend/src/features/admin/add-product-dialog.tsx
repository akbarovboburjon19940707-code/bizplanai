"use client";

import { useState } from "react";
import type { Category } from "@/features/catalog/types";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { formatNumber, parseNumber } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import { FormAlert, FormField, inputClass } from "@/shared/ui/form-field";
import { Modal } from "@/shared/ui/modal";
import type { AdminProduct } from "./types";

const t = uz.admin.catalog;
type Step = keyof typeof t.creating;

export async function uploadProductFile(id: string, kind: "file" | "image", file: File): Promise<AdminProduct> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest<AdminProduct>(`/v1/admin/catalog/products/${encodeURIComponent(id)}/${kind}`, { method: "POST", body });
}

/**
 * Yangi reja: yaratish (yashirin) -> PDF -> rasm -> faollashtirish. Backend faylsiz rejani faollashtirmaydi,
 * shuning uchun biror qadam yiqilsa reja yashirin qoladi va admin faylni ro'yxatdan qayta yuklaydi.
 */
export function AddProductDialog({ open, onClose, categories, onCreated }: {
  open: boolean;
  onClose: () => void;
  categories: Category[];
  onCreated: (p: AdminProduct) => void;
}) {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [price, setPrice] = useState("");
  const [description, setDescription] = useState("");
  const [pdf, setPdf] = useState<File | null>(null);
  const [image, setImage] = useState<File | null>(null);
  const [publish, setPublish] = useState(true);
  const [step, setStep] = useState<Step | null>(null);
  const [error, setError] = useState<string | null>(null);
  const priceNum = parseNumber(price);

  const reset = () => {
    setTitle(""); setPrice(""); setDescription(""); setPdf(null); setImage(null); setPublish(true); setError(null);
  };

  const submit = async () => {
    const cat = category || categories[0]?.key;
    if (title.trim().length < 2) return setError(t.titleMin);
    if (!priceNum || priceNum <= 0 || priceNum > 100_000_000 || !Number.isInteger(priceNum)) return setError(t.priceInvalid);
    if (!pdf) return setError(t.pdfRequired);
    setError(null);
    let created: AdminProduct | null = null;
    try {
      setStep("product");
      created = await apiRequest<AdminProduct>("/v1/admin/catalog/products", {
        method: "POST",
        body: JSON.stringify({ title: title.trim(), category_key: cat, price_som: priceNum, description: description.trim() }),
      });
      setStep("pdf");
      created = await uploadProductFile(created.id, "file", pdf);
      if (image) {
        setStep("image");
        created = await uploadProductFile(created.id, "image", image);
      }
      if (publish) {
        setStep("publish");
        created = await apiRequest<AdminProduct>(`/v1/admin/catalog/products/${encodeURIComponent(created.id)}`, {
          method: "PATCH", body: JSON.stringify({ is_active: true }),
        });
      }
      onCreated(created);
      reset();
      onClose();
    } catch (e) {
      const msg = e instanceof ApiError && e.message ? e.message : uz.authForms.genericError;
      setError(created ? `${t.partial} (${msg})` : msg);
      if (created) onCreated(created);
    } finally {
      setStep(null);
    }
  };

  const busy = step !== null;
  return (
    <Modal open={open} onClose={() => !busy && onClose()} title={t.addTitle} closeLabel={t.cancel}>
      <form className="flex flex-col gap-3" noValidate onSubmit={(e) => { e.preventDefault(); void submit(); }}>
        {error ? <FormAlert>{error}</FormAlert> : null}
        <FormField id="np-title" label={t.title}>
          <input id="np-title" className={inputClass} maxLength={255} value={title} onChange={(e) => setTitle(e.target.value)} />
        </FormField>
        <div className="grid gap-3 sm:grid-cols-2">
          <FormField id="np-cat" label={t.category}>
            <select id="np-cat" className={inputClass} value={category || categories[0]?.key || ""} onChange={(e) => setCategory(e.target.value)}>
              {categories.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
            </select>
          </FormField>
          <FormField id="np-price" label={t.price}>
            <input id="np-price" className={`${inputClass} text-right tabular-nums`} inputMode="numeric" value={price}
              onChange={(e) => setPrice(formatNumber(parseNumber(e.target.value)))} />
          </FormField>
        </div>
        <FormField id="np-desc" label={t.description}>
          <textarea id="np-desc" rows={3} maxLength={5000} className={`${inputClass} min-h-24 py-2`} value={description}
            onChange={(e) => setDescription(e.target.value)} />
        </FormField>
        <FormField id="np-pdf" label={t.pdf}>
          <input id="np-pdf" type="file" accept="application/pdf,.pdf" className="text-sm"
            onChange={(e) => setPdf(e.target.files?.[0] ?? null)} />
        </FormField>
        <FormField id="np-img" label={t.image}>
          <input id="np-img" type="file" accept="image/png,image/jpeg,image/webp" className="text-sm"
            onChange={(e) => setImage(e.target.files?.[0] ?? null)} />
        </FormField>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" className="size-4 accent-[#2563eb]" checked={publish} onChange={(e) => setPublish(e.target.checked)} />
          {t.publish}
        </label>
        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={busy}>{t.cancel}</Button>
          <Button type="submit" disabled={busy} aria-busy={busy}>{step ? t.creating[step] : t.create}</Button>
        </div>
      </form>
    </Modal>
  );
}

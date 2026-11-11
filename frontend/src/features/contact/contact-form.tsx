"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { useAuth } from "@/features/auth/auth-context";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { applyApiError } from "@/shared/api/form-errors";
import { formatLocalPhone, toE164 } from "@/shared/lib/phone";
import { useCooldown } from "@/shared/lib/use-cooldown";
import { Button } from "@/shared/ui/button";
import { FormAlert, FormField, fieldAria, inputClass } from "@/shared/ui/form-field";
import { PhoneInput } from "@/shared/ui/phone-input";
import { TOPICS, contactSchema, type ContactValues } from "./schema";

const t = uz.contact;
const FIELDS = ["name", "phone", "topic", "message"] as const;
const EMPTY: ContactValues = { name: "", phone: "", topic: "other", message: "", website: "" };

/** Aloqa formasi: POST /v1/contact. Kirgan foydalanuvchi uchun ism va raqam oldindan to'ldiriladi. */
export function ContactForm() {
  const { user } = useAuth();
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const cooldown = useCooldown();
  const form = useForm<ContactValues>({
    resolver: zodResolver(contactSchema),
    defaultValues: EMPTY,
    mode: "onSubmit",
    reValidateMode: "onChange",
  });
  const { errors, isSubmitting } = form.formState;
  const messageLength = useWatch({ control: form.control, name: "message" })?.length ?? 0;

  useEffect(() => {
    if (!user) return;
    if (!form.getValues("name") && user.first_name) form.setValue("name", user.first_name);
    if (!form.getValues("phone") && user.phone) form.setValue("phone", formatLocalPhone(user.phone));
  }, [user, form]);

  const onSubmit = form.handleSubmit(async (values) => {
    setFormError(null);
    try {
      await apiRequest("/v1/contact", {
        method: "POST",
        body: JSON.stringify({ ...values, phone: toE164(values.phone) }),
      });
      setSent(true);
      form.reset({ ...EMPTY, name: values.name, phone: values.phone });
    } catch (error) {
      if (error instanceof ApiError && error.code === "rate_limited") cooldown.start(60);
      setFormError(applyApiError(error, form.setError, FIELDS));
    }
  });

  if (sent) {
    return (
      <div className="flex flex-col items-start gap-4" aria-live="polite">
        <FormAlert tone="success">
          <strong className="block font-semibold">{t.sentTitle}</strong>
          {t.sentText}
        </FormAlert>
        <Button type="button" variant="outline" onClick={() => setSent(false)}>
          {t.sendAnother}
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={(e) => void onSubmit(e)} noValidate className="flex flex-col gap-4">
      {formError ? <FormAlert>{formError}</FormAlert> : null}
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField id="contact-name" label={t.name} error={errors.name?.message}>
          <input id="contact-name" className={inputClass} autoComplete="name" maxLength={100}
            {...form.register("name")} {...fieldAria("contact-name", errors.name?.message)} />
        </FormField>
        <Controller
          control={form.control}
          name="phone"
          render={({ field }) => (
            <FormField id="contact-phone" label={t.phoneField} hint={t.phoneHint} error={errors.phone?.message}>
              <PhoneInput id="contact-phone" {...field} {...fieldAria("contact-phone", errors.phone?.message, t.phoneHint)} />
            </FormField>
          )}
        />
      </div>
      <FormField id="contact-topic" label={t.topic} error={errors.topic?.message}>
        <select id="contact-topic" className={inputClass} {...form.register("topic")}>
          {TOPICS.map((key) => (
            <option key={key} value={key}>{t.topics[key]}</option>
          ))}
        </select>
      </FormField>
      <FormField id="contact-message" label={t.message} hint={t.messageHint} error={errors.message?.message}>
        <textarea id="contact-message" rows={6} maxLength={2000} className={`${inputClass} min-h-36 resize-y py-3`}
          {...form.register("message")} {...fieldAria("contact-message", errors.message?.message, t.messageHint)} />
      </FormField>
      <p className="-mt-2 self-end text-xs tabular-nums text-muted">{messageLength} / 2000</p>
      {/* Bot tuzog'i: ekranda ham, ekran o'quvchida ham ko'rinmaydi */}
      <div aria-hidden="true" className="absolute -left-[10000px] h-px w-px overflow-hidden">
        <label htmlFor="contact-website">Website</label>
        <input id="contact-website" tabIndex={-1} autoComplete="off" {...form.register("website")} />
      </div>
      <Button type="submit" size="lg" className="sm:self-start" disabled={isSubmitting || cooldown.active} aria-busy={isSubmitting}>
        {isSubmitting ? t.submitting : t.submit}
      </Button>
      {cooldown.active ? (
        <p className="text-xs text-muted" aria-live="polite">{uz.authForms.retryIn(cooldown.left)}</p>
      ) : null}
    </form>
  );
}

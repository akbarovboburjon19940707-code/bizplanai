"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { uz } from "@/messages/uz";
import { apiRequest, updateCurrentUser } from "@/shared/api/client";
import { applyApiError } from "@/shared/api/form-errors";
import type { components } from "@/shared/api/schema";
import { formatPhone } from "@/shared/lib/phone";
import { Button } from "@/shared/ui/button";
import { FormAlert, FormField, fieldAria, inputClass } from "@/shared/ui/form-field";
import { profileSchema, type ProfileValues } from "./schemas";

type UserOut = components["schemas"]["UserOut"];
const t = uz.account.profile;
const FIELDS = ["first_name", "last_name", "email"] as const;

const toValues = (u: UserOut): ProfileValues => ({ first_name: u.first_name, last_name: u.last_name, email: u.email ?? "" });

export function ProfileForm({ user, onSaved }: { user: UserOut; onSaved: (user: UserOut) => void }) {
  const [message, setMessage] = useState<{ tone: "error" | "success"; text: string } | null>(null);
  const form = useForm<ProfileValues>({ resolver: zodResolver(profileSchema), defaultValues: toValues(user) });
  const { errors, isSubmitting, isDirty } = form.formState;

  const onSubmit = form.handleSubmit(async (values) => {
    setMessage(null);
    try {
      // API null qiymatni "o'zgartirmaslik" deb tushunadi: bo'sh email yuborilmaydi (CONTRACT_REQUESTS.md)
      const updated = await apiRequest<UserOut>("/v1/me", {
        method: "PATCH",
        body: JSON.stringify({ first_name: values.first_name, last_name: values.last_name, email: values.email || null }),
      });
      form.reset(toValues(updated));
      updateCurrentUser(updated);
      onSaved(updated);
      setMessage({ tone: "success", text: t.saved });
    } catch (error) {
      const text = applyApiError(error, form.setError, FIELDS);
      if (text) setMessage({ tone: "error", text });
    }
  });

  return (
    <section className="rounded-card border border-border bg-white p-5 shadow-soft sm:p-6">
      <h2 className="text-base font-bold text-ink">{t.title}</h2>
      <dl className="mt-4 space-y-1 text-sm">
        {user.phone ? (
          <div className="flex justify-between gap-2"><dt className="text-muted">{t.phone}</dt><dd className="font-medium tabular-nums">{formatPhone(user.phone)}</dd></div>
        ) : null}
        {user.telegram_username ? (
          <div className="flex justify-between gap-2"><dt className="text-muted">{t.telegram}</dt><dd className="font-medium">@{user.telegram_username}</dd></div>
        ) : null}
      </dl>
      <form onSubmit={(e) => void onSubmit(e)} noValidate className="mt-4 flex flex-col gap-4">
        {message ? <FormAlert tone={message.tone}>{message.text}</FormAlert> : null}
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField id="pf-first" label={t.firstName} error={errors.first_name?.message}>
            <input id="pf-first" className={inputClass} autoComplete="given-name" maxLength={100}
              {...form.register("first_name")} {...fieldAria("pf-first", errors.first_name?.message)} />
          </FormField>
          <FormField id="pf-last" label={t.lastName} error={errors.last_name?.message}>
            <input id="pf-last" className={inputClass} autoComplete="family-name" maxLength={100}
              {...form.register("last_name")} {...fieldAria("pf-last", errors.last_name?.message)} />
          </FormField>
        </div>
        <FormField id="pf-email" label={t.email} error={errors.email?.message}>
          <input id="pf-email" type="email" className={inputClass} autoComplete="email" maxLength={254}
            {...form.register("email")} {...fieldAria("pf-email", errors.email?.message)} />
        </FormField>
        <Button type="submit" disabled={!isDirty || isSubmitting} className="self-start">
          {isSubmitting ? t.saving : t.save}
        </Button>
      </form>
    </section>
  );
}

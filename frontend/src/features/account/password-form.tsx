"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { applyApiError } from "@/shared/api/form-errors";
import { useCooldown } from "@/shared/lib/use-cooldown";
import { Button } from "@/shared/ui/button";
import { FormAlert, FormField, fieldAria } from "@/shared/ui/form-field";
import { PasswordInput } from "@/shared/ui/password-input";
import { passwordSchema, type PasswordValues } from "./schemas";

const t = uz.account.password;
const FIELDS = ["current_password", "new_password"] as const;
const EMPTY: PasswordValues = { current_password: "", new_password: "", confirm: "" };

export function PasswordForm() {
  const [message, setMessage] = useState<{ tone: "error" | "success"; text: string } | null>(null);
  const cooldown = useCooldown();
  const form = useForm<PasswordValues>({ resolver: zodResolver(passwordSchema), defaultValues: EMPTY, mode: "onSubmit", reValidateMode: "onChange" });
  const { errors, isSubmitting } = form.formState;

  const onSubmit = form.handleSubmit(async (values) => {
    setMessage(null);
    try {
      await apiRequest<void>("/v1/me/password", {
        method: "POST",
        body: JSON.stringify({ current_password: values.current_password || null, new_password: values.new_password }),
      });
      form.reset(EMPTY);
      setMessage({ tone: "success", text: t.done });
    } catch (error) {
      if (error instanceof ApiError && error.code === "wrong_password") {
        return form.setError("current_password", { message: error.message }, { shouldFocus: true });
      }
      if (error instanceof ApiError && error.code === "rate_limited") cooldown.start(10);
      const text = applyApiError(error, form.setError, FIELDS);
      if (text) setMessage({ tone: "error", text });
    }
  });

  return (
    <section className="rounded-card border border-border bg-white p-5 shadow-soft sm:p-6">
      <h2 className="text-base font-bold text-ink">{t.title}</h2>
      <form onSubmit={(e) => void onSubmit(e)} noValidate className="mt-4 flex flex-col gap-4">
        {message ? <FormAlert tone={message.tone}>{message.text}</FormAlert> : null}
        {/* Parol menejerlari uchun: qaysi hisobning paroli ekani */}
        <input type="text" name="username" autoComplete="username" hidden readOnly />
        <FormField id="pw-current" label={t.current} hint={t.currentHint} error={errors.current_password?.message}>
          <PasswordInput id="pw-current" autoComplete="current-password"
            {...form.register("current_password")} {...fieldAria("pw-current", errors.current_password?.message, t.currentHint)} />
        </FormField>
        <FormField id="pw-new" label={t.next} hint={uz.authForms.passwordMin} error={errors.new_password?.message}>
          <PasswordInput id="pw-new" autoComplete="new-password"
            {...form.register("new_password")} {...fieldAria("pw-new", errors.new_password?.message, uz.authForms.passwordMin)} />
        </FormField>
        <FormField id="pw-confirm" label={t.confirm} error={errors.confirm?.message}>
          <PasswordInput id="pw-confirm" autoComplete="new-password"
            {...form.register("confirm")} {...fieldAria("pw-confirm", errors.confirm?.message)} />
        </FormField>
        <Button type="submit" variant="outline" disabled={isSubmitting || cooldown.active} className="self-start">
          {isSubmitting ? t.submitting : cooldown.active ? uz.authForms.retryIn(cooldown.left) : t.submit}
        </Button>
      </form>
    </section>
  );
}

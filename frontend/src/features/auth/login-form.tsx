"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { uz } from "@/messages/uz";
import { apiRequest, startSession } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { applyApiError } from "@/shared/api/form-errors";
import type { components } from "@/shared/api/schema";
import { toE164 } from "@/shared/lib/phone";
import { useCooldown } from "@/shared/lib/use-cooldown";
import { Button } from "@/shared/ui/button";
import { FormAlert, FormField, fieldAria, inputClass } from "@/shared/ui/form-field";
import { PasswordInput } from "@/shared/ui/password-input";
import { PhoneInput } from "@/shared/ui/phone-input";
import { loginSchema, type LoginValues } from "./schemas";

type TokenOut = components["schemas"]["TokenOut"];
const t = uz.authForms;
const FIELDS = ["phone", "password", "totp_code"] as const;

export function LoginForm() {
  const [needTotp, setNeedTotp] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const cooldown = useCooldown();
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { phone: "", password: "", totp_code: "" },
    mode: "onTouched",
  });
  const { errors, isSubmitting } = form.formState;

  useEffect(() => {
    if (needTotp) form.setFocus("totp_code");
  }, [needTotp, form]);

  const onSubmit = form.handleSubmit(async (values) => {
    setFormError(null);
    try {
      const token = await apiRequest<TokenOut>("/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({
          phone: toE164(values.phone),
          password: values.password,
          totp_code: needTotp && values.totp_code ? values.totp_code : null,
        }),
      });
      startSession(token); // sahifa useRedirectWhenSignedIn orqali o'zi o'tadi
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "totp_required") {
          setNeedTotp(true);
          return setFormError(null);
        }
        if (error.code === "totp_invalid") {
          form.setValue("totp_code", "");
          return form.setError("totp_code", { message: error.message }, { shouldFocus: true });
        }
        if (error.code === "rate_limited") cooldown.start(10);
      }
      setFormError(applyApiError(error, form.setError, FIELDS));
    }
  });

  const busy = isSubmitting || cooldown.active;

  return (
    <form onSubmit={(e) => void onSubmit(e)} noValidate className="flex flex-col gap-4">
      {formError ? <FormAlert>{formError}</FormAlert> : null}
      <Controller
        control={form.control}
        name="phone"
        render={({ field }) => (
          <FormField id="login-phone" label={t.phone} error={errors.phone?.message}>
            <PhoneInput id="login-phone" autoFocus {...field} {...fieldAria("login-phone", errors.phone?.message)} />
          </FormField>
        )}
      />
      <FormField id="login-password" label={t.password} error={errors.password?.message}>
        <PasswordInput
          id="login-password"
          autoComplete="current-password"
          {...form.register("password")}
          {...fieldAria("login-password", errors.password?.message)}
        />
      </FormField>
      {needTotp ? (
        <FormField id="login-totp" label={t.login.totp} hint={t.login.totpHint} error={errors.totp_code?.message}>
          <input
            id="login-totp"
            className={`${inputClass} text-center text-lg tracking-[0.5em] tabular-nums`}
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            {...form.register("totp_code", {
              onChange: (e: { target: HTMLInputElement }) => {
                e.target.value = e.target.value.replace(/\D/g, "").slice(0, 6);
              },
            })}
            {...fieldAria("login-totp", errors.totp_code?.message, t.login.totpHint)}
          />
        </FormField>
      ) : null}
      <Button type="submit" size="lg" disabled={busy} aria-busy={isSubmitting}>
        {isSubmitting ? t.login.submitting : t.login.submit}
      </Button>
      {cooldown.active ? (
        <p className="text-center text-xs text-muted" aria-live="polite">
          {t.retryIn(cooldown.left)}
        </p>
      ) : null}
    </form>
  );
}

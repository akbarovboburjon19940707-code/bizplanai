"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
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
import { registerSchema, type RegisterValues } from "./schemas";

type TokenOut = components["schemas"]["TokenOut"];
const t = uz.authForms;
const FIELDS = ["first_name", "phone", "password"] as const;

export function RegisterForm({ loginHref }: { loginHref: string }) {
  const [formError, setFormError] = useState<string | null>(null);
  const [phoneTaken, setPhoneTaken] = useState(false);
  const cooldown = useCooldown();
  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { first_name: "", phone: "", password: "", password_confirm: "" },
    mode: "onTouched",
  });
  const { errors, isSubmitting } = form.formState;

  const onSubmit = form.handleSubmit(async (values) => {
    setFormError(null);
    setPhoneTaken(false);
    try {
      const token = await apiRequest<TokenOut>("/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ phone: toE164(values.phone), password: values.password, first_name: values.first_name }),
      });
      startSession(token);
    } catch (error) {
      if (error instanceof ApiError && error.code === "phone_taken") {
        setPhoneTaken(true);
        return form.setError("phone", { message: t.register.phoneTaken }, { shouldFocus: true });
      }
      if (error instanceof ApiError && error.code === "rate_limited") cooldown.start(10);
      setFormError(applyApiError(error, form.setError, FIELDS));
    }
  });

  return (
    <form onSubmit={(e) => void onSubmit(e)} noValidate className="flex flex-col gap-4">
      {formError ? <FormAlert>{formError}</FormAlert> : null}
      <FormField id="reg-name" label={t.firstName} hint={t.firstNameHint} error={errors.first_name?.message}>
        <input
          id="reg-name"
          className={inputClass}
          autoComplete="given-name"
          maxLength={100}
          {...form.register("first_name")}
          {...fieldAria("reg-name", errors.first_name?.message, t.firstNameHint)}
        />
      </FormField>
      <Controller
        control={form.control}
        name="phone"
        render={({ field }) => (
          <FormField id="reg-phone" label={t.phone} error={errors.phone?.message}>
            <PhoneInput id="reg-phone" {...field} {...fieldAria("reg-phone", errors.phone?.message)} />
          </FormField>
        )}
      />
      {phoneTaken ? (
        <Link href={loginHref} className="-mt-2 text-sm font-semibold text-brand hover:underline">
          {t.register.phoneTakenAction} →
        </Link>
      ) : null}
      <FormField id="reg-password" label={t.password} hint={t.passwordMin} error={errors.password?.message}>
        <PasswordInput
          id="reg-password"
          autoComplete="new-password"
          {...form.register("password")}
          {...fieldAria("reg-password", errors.password?.message, t.passwordMin)}
        />
      </FormField>
      <FormField id="reg-password2" label={t.passwordConfirm} error={errors.password_confirm?.message}>
        <PasswordInput
          id="reg-password2"
          autoComplete="new-password"
          {...form.register("password_confirm")}
          {...fieldAria("reg-password2", errors.password_confirm?.message)}
        />
      </FormField>
      <Button type="submit" size="lg" disabled={isSubmitting || cooldown.active} aria-busy={isSubmitting}>
        {isSubmitting ? t.register.submitting : t.register.submit}
      </Button>
      {cooldown.active ? (
        <p className="text-center text-xs text-muted" aria-live="polite">
          {t.retryIn(cooldown.left)}
        </p>
      ) : null}
    </form>
  );
}

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
import { Button } from "@/shared/ui/button";
import { FormAlert, FormField, fieldAria } from "@/shared/ui/form-field";
import { PasswordInput } from "@/shared/ui/password-input";
import { PhoneInput } from "@/shared/ui/phone-input";
import { AuthCard, AuthSkeleton } from "./auth-card";
import { newPasswordSchema, resetPhoneSchema, type NewPasswordValues, type ResetPhoneValues } from "./schemas";
import { usePasswordReset } from "./use-password-reset";
import { useRedirectWhenSignedIn } from "./use-redirect-when-signed-in";

type CompleteOut = components["schemas"]["PasswordResetCompleteOut"];
const t = uz.authForms;
const r = t.reset;

function PhoneStep({ busy, onSubmit }: { busy: boolean; onSubmit: (phone: string) => void }) {
  const form = useForm<ResetPhoneValues>({
    resolver: zodResolver(resetPhoneSchema),
    defaultValues: { phone: "" },
    mode: "onSubmit",
    reValidateMode: "onChange",
  });
  const error = form.formState.errors.phone?.message;
  return (
    <form
      noValidate
      className="flex flex-col gap-4"
      onSubmit={(e) => void form.handleSubmit((v) => onSubmit(toE164(v.phone)))(e)}
    >
      <Controller
        control={form.control}
        name="phone"
        render={({ field }) => (
          <FormField id="reset-phone" label={t.phone} hint={r.phoneHint} error={error}>
            <PhoneInput id="reset-phone" autoFocus {...field} {...fieldAria("reset-phone", error, r.phoneHint)} />
          </FormField>
        )}
      />
      <Button type="submit" size="lg" disabled={busy} aria-busy={busy}>
        {busy ? r.starting : r.start}
      </Button>
    </form>
  );
}

function NewPasswordStep({ token, onAdminDone, onInvalid }: {
  token: string;
  onAdminDone: () => void;
  onInvalid: () => void;
}) {
  const [formError, setFormError] = useState<string | null>(null);
  const form = useForm<NewPasswordValues>({
    resolver: zodResolver(newPasswordSchema),
    defaultValues: { password: "", password_confirm: "" },
    mode: "onSubmit",
    reValidateMode: "onChange",
  });
  const { errors, isSubmitting } = form.formState;
  const submit = form.handleSubmit(async (v) => {
    setFormError(null);
    try {
      const res = await apiRequest<CompleteOut>("/v1/auth/password-reset/complete", {
        method: "POST",
        body: JSON.stringify({ token, new_password: v.password }),
      });
      if (res.session) startSession(res.session); // sahifa useRedirectWhenSignedIn orqali o'zi o'tadi
      else onAdminDone();
    } catch (error) {
      if (error instanceof ApiError && error.code === "reset_invalid") return onInvalid();
      setFormError(applyApiError(error, form.setError, ["password"]));
    }
  });
  return (
    <form noValidate className="flex flex-col gap-4" onSubmit={(e) => void submit(e)}>
      <FormAlert tone="success">{r.verified}</FormAlert>
      {formError ? <FormAlert>{formError}</FormAlert> : null}
      <FormField id="reset-pw" label={r.newPassword} hint={t.passwordMin} error={errors.password?.message}>
        <PasswordInput
          id="reset-pw"
          autoFocus
          autoComplete="new-password"
          {...form.register("password")}
          {...fieldAria("reset-pw", errors.password?.message, t.passwordMin)}
        />
      </FormField>
      <FormField id="reset-pw2" label={t.passwordConfirm} error={errors.password_confirm?.message}>
        <PasswordInput
          id="reset-pw2"
          autoComplete="new-password"
          {...form.register("password_confirm")}
          {...fieldAria("reset-pw2", errors.password_confirm?.message)}
        />
      </FormField>
      <Button type="submit" size="lg" disabled={isSubmitting} aria-busy={isSubmitting}>
        {isSubmitting ? r.submitting : r.submit}
      </Button>
    </form>
  );
}

/** /parol-tiklash: telefon -> Telegram botda raqamni tasdiqlash -> yangi parol. */
export function PasswordResetPage() {
  const { status } = useRedirectWhenSignedIn();
  const { state, start, reset, setState } = usePasswordReset();
  const [adminDone, setAdminDone] = useState(false);
  if (status !== "guest") return <AuthSkeleton />;

  let body;
  if (adminDone) {
    body = (
      <div className="flex flex-col gap-4">
        <FormAlert tone="success">{r.doneAdmin}</FormAlert>
        <Button asChild size="lg">
          <Link href="/kirish/">{r.toLogin}</Link>
        </Button>
      </div>
    );
  } else if (state.phase === "waiting") {
    body = (
      <div className="flex flex-col gap-3 rounded-control border border-blue-100 bg-blue-50 p-4" aria-live="polite">
        <p className="text-sm text-blue-900">{r.waiting}</p>
        <div className="flex flex-wrap items-center gap-3">
          <Button asChild size="md">
            <a href={state.botUrl} target="_blank" rel="noopener noreferrer">
              {r.openBot}
            </a>
          </Button>
          <Button type="button" variant="ghost" onClick={reset}>
            {r.cancel}
          </Button>
          <span className="ml-auto size-4 animate-spin rounded-full border-2 border-brand border-t-transparent" aria-hidden="true" />
        </div>
      </div>
    );
  } else if (state.phase === "verified") {
    body = (
      <NewPasswordStep
        token={state.token}
        onAdminDone={() => setAdminDone(true)}
        onInvalid={() => setState({ phase: "expired" })}
      />
    );
  } else if (state.phase === "mismatch" || state.phase === "expired") {
    body = (
      <div className="flex flex-col gap-4" aria-live="polite">
        <FormAlert tone={state.phase === "expired" ? "info" : undefined}>{state.phase === "mismatch" ? r.mismatch : r.expired}</FormAlert>
        <Button type="button" size="lg" onClick={reset}>
          {r.retry}
        </Button>
      </div>
    );
  } else {
    body = (
      <div className="flex flex-col gap-4">
        {state.phase === "error" ? <FormAlert>{state.message || t.genericError}</FormAlert> : null}
        <PhoneStep busy={state.phase === "preparing"} onSubmit={(phone) => void start(phone)} />
        <p className="text-xs text-muted">{r.noTelegram}</p>
      </div>
    );
  }

  return (
    <AuthCard
      title={r.title}
      subtitle={r.subtitle}
      footer={
        <>
          {r.remember}{" "}
          <Link href="/kirish/" className="font-semibold text-brand hover:underline">
            {t.login.submit}
          </Link>
        </>
      }
    >
      {body}
    </AuthCard>
  );
}

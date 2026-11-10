"use client";

import Link from "next/link";
import { uz } from "@/messages/uz";
import { AuthCard, AuthSkeleton, OrDivider } from "./auth-card";
import { LoginForm } from "./login-form";
import { TelegramLogin } from "./telegram-login";
import { useRedirectWhenSignedIn } from "./use-redirect-when-signed-in";

const t = uz.authForms;

export function LoginPage() {
  const { status, next } = useRedirectWhenSignedIn();
  if (status !== "guest") return <AuthSkeleton />;
  return (
    <AuthCard
      title={t.login.title}
      subtitle={t.login.subtitle}
      footer={
        <>
          {t.login.noAccount}{" "}
          <Link href={`/royxat/?next=${encodeURIComponent(next)}`} className="font-semibold text-brand hover:underline">
            {t.login.toRegister}
          </Link>
        </>
      }
    >
      <LoginForm />
      <OrDivider label={t.or} />
      <TelegramLogin />
    </AuthCard>
  );
}

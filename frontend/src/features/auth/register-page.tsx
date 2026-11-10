"use client";

import Link from "next/link";
import { uz } from "@/messages/uz";
import { AuthCard, AuthSkeleton, OrDivider } from "./auth-card";
import { RegisterForm } from "./register-form";
import { TelegramLogin } from "./telegram-login";
import { useRedirectWhenSignedIn } from "./use-redirect-when-signed-in";

const t = uz.authForms;

export function RegisterPage() {
  const { status, next } = useRedirectWhenSignedIn();
  if (status !== "guest") return <AuthSkeleton />;
  const loginHref = `/kirish/?next=${encodeURIComponent(next)}`;
  return (
    <AuthCard
      title={t.register.title}
      subtitle={t.register.subtitle}
      footer={
        <>
          {t.register.haveAccount}{" "}
          <Link href={loginHref} className="font-semibold text-brand hover:underline">
            {t.register.toLogin}
          </Link>
        </>
      }
    >
      <RegisterForm loginHref={loginHref} />
      <OrDivider label={t.or} />
      <TelegramLogin />
    </AuthCard>
  );
}

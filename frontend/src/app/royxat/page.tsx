import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthSkeleton } from "@/features/auth/auth-card";
import { RegisterPage } from "@/features/auth/register-page";
import { uz } from "@/messages/uz";

export const metadata: Metadata = {
  title: `${uz.authForms.register.title} | ${uz.appName}`,
  robots: { index: false },
};

export default function Page() {
  return (
    <Suspense fallback={<AuthSkeleton />}>
      <RegisterPage />
    </Suspense>
  );
}

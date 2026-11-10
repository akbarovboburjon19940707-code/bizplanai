import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthSkeleton } from "@/features/auth/auth-card";
import { LoginPage } from "@/features/auth/login-page";
import { uz } from "@/messages/uz";

export const metadata: Metadata = {
  title: `${uz.authForms.login.title} | ${uz.appName}`,
  robots: { index: false },
};

export default function Page() {
  return (
    <Suspense fallback={<AuthSkeleton />}>
      <LoginPage />
    </Suspense>
  );
}

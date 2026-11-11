import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthSkeleton } from "@/features/auth/auth-card";
import { PasswordResetPage } from "@/features/auth/password-reset-page";
import { uz } from "@/messages/uz";

export const metadata: Metadata = {
  title: `${uz.authForms.reset.title} | ${uz.appName}`,
  robots: { index: false },
};

export default function Page() {
  return (
    <Suspense fallback={<AuthSkeleton />}>
      <PasswordResetPage />
    </Suspense>
  );
}

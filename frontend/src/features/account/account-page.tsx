"use client";

import Link from "next/link";
import { RequireAuth } from "@/features/auth/require-auth";
import { uz } from "@/messages/uz";
import { useApi } from "@/shared/api/use-api";
import type { components } from "@/shared/api/schema";
import { Button } from "@/shared/ui/button";
import { RecentPayments, RecentPlans } from "./history-lists";
import { PasswordForm } from "./password-form";
import { ProfileForm } from "./profile-form";
import { SubscriptionCard } from "./subscription-card";

type MeOut = components["schemas"]["MeOut"];
const t = uz.account;

function AccountSkeleton() {
  return (
    <div className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1.4fr_1fr] lg:px-8" aria-busy="true">
      <div className="space-y-6">
        <div className="h-9 w-56 animate-pulse rounded bg-slate-200" />
        <div className="h-48 animate-pulse rounded-card bg-white" />
        <div className="h-56 animate-pulse rounded-card bg-white" />
      </div>
      <div className="space-y-6 lg:pt-16">
        <div className="h-64 animate-pulse rounded-card bg-white" />
      </div>
    </div>
  );
}

function AccountView() {
  const me = useApi<MeOut>("/v1/me");

  if (me.loading && !me.data) return <AccountSkeleton />;
  if (!me.data) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16 text-center">
        <p className="text-sm text-red-600">{me.error?.message || t.loadError}</p>
        <Button className="mt-4" variant="outline" onClick={me.reload}>{t.retry}</Button>
      </div>
    );
  }

  const { user, subscription } = me.data;
  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted">{t.title}</p>
          <h1 className="font-[var(--font-outfit)] text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            {t.greeting(user.first_name)}
          </h1>
        </div>
        <Button asChild size="lg">
          <Link href="/dashboard/">{t.newPlan}</Link>
        </Button>
      </div>
      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="flex min-w-0 flex-col gap-6">
          <SubscriptionCard subscription={subscription} credits={user.plan_credits} />
          <RecentPlans />
          <RecentPayments />
        </div>
        <div className="flex min-w-0 flex-col gap-6">
          <ProfileForm user={user} onSaved={(u) => me.replace({ ...me.data!, user: u })} />
          <PasswordForm hasPassword={user.has_password ?? true} onChanged={me.reload} />
        </div>
      </div>
    </div>
  );
}

export function AccountPage() {
  return (
    <RequireAuth fallback={<AccountSkeleton />}>
      <AccountView />
    </RequireAuth>
  );
}

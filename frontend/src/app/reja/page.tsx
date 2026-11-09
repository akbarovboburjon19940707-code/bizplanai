import type { Metadata } from "next";
import { Suspense } from "react";
import { PlanStatus } from "@/features/plans/plan-status";
import { uz } from "@/messages/uz";

export const metadata: Metadata = { title: `${uz.plans.plan.title} | ${uz.appName}` };

export default function PlanPage() {
  return (
    <Suspense fallback={null}>
      <PlanStatus />
    </Suspense>
  );
}

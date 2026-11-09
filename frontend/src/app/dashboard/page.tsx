import type { Metadata } from "next";
import { PlanWizard } from "@/features/plans/plan-wizard";
import { uz } from "@/messages/uz";

export const metadata: Metadata = { title: `${uz.plans.title} | ${uz.appName}` };

export default function DashboardPage() {
  return <PlanWizard />;
}

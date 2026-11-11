import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AdminShell } from "@/features/admin/admin-shell";
import { uz } from "@/messages/uz";

export const metadata: Metadata = { title: `${uz.admin.title} | ${uz.appName}`, robots: { index: false, follow: false } };

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}

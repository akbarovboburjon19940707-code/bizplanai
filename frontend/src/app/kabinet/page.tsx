import type { Metadata } from "next";
import { AccountPage } from "@/features/account/account-page";
import { uz } from "@/messages/uz";

export const metadata: Metadata = { title: `${uz.account.title} | ${uz.appName}`, robots: { index: false } };

export default function Page() {
  return <AccountPage />;
}

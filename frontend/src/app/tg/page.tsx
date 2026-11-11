import type { Metadata } from "next";
import { MiniApp } from "@/features/telegram/mini-app";
import { uz } from "@/messages/uz";

export const metadata: Metadata = { title: uz.appName, robots: { index: false } };

export default function Page() {
  return <MiniApp />;
}

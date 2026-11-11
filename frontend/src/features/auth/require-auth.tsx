"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useAuth } from "./auth-context";

/** Faqat kirgan foydalanuvchi uchun: mehmonni `/kirish/?next=<joriy sahifa>` ga o'tkazadi. */
export function RequireAuth({ children, fallback }: { children: ReactNode; fallback: ReactNode }) {
  const { status, signedOutByUser } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status !== "guest") return;
    router.replace(signedOutByUser ? "/" : `/kirish/?next=${encodeURIComponent(pathname)}`);
  }, [status, signedOutByUser, pathname, router]);

  return status === "authenticated" ? <>{children}</> : <>{fallback}</>;
}

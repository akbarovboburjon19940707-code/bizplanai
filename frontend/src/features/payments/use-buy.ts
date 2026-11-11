"use client";

import { usePathname, useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { useAuth } from "@/features/auth/auth-context";

/** "Sotib olish" tugmasi: mehmonni kirishga (shu sahifaga qaytish bilan), kirganga to'lov oynasini ochadi. */
export function useBuy() {
  const { status } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const start = useCallback(() => {
    if (status === "authenticated") return setOpen(true);
    router.push(`/kirish/?next=${encodeURIComponent(pathname)}`);
  }, [status, router, pathname]);

  return { open, start, close: useCallback(() => setOpen(false), []), ready: status !== "loading" };
}

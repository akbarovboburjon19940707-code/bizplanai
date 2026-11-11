"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import { safeNextPath } from "@/shared/lib/safe-next";
import { useAuth } from "./auth-context";

/** Kirish/ro'yxat sahifalarida: sessiya bo'lsa `?next=` (xavfsiz) yoki kabinetga o'tkazadi. */
export function useRedirectWhenSignedIn() {
  const router = useRouter();
  const next = safeNextPath(useSearchParams().get("next"));
  const { status } = useAuth();

  useEffect(() => {
    if (status === "authenticated") router.replace(next);
  }, [status, next, router]);

  return { status, next };
}

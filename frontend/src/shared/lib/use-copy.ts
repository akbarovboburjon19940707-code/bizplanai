"use client";

import { useCallback, useState } from "react";

/** Matnni buferga nusxalash; `copied` 2 soniya true bo'lib turadi. */
export function useCopy() {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Buferga ruxsat yo'q (masalan, http): foydalanuvchi qo'lda nusxalaydi
    }
  }, []);
  return { copied, copy };
}

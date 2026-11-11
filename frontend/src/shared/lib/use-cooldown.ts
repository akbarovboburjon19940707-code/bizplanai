"use client";

import { useCallback, useEffect, useState } from "react";

/** `429 rate_limited` dan keyin tugmani bir necha soniya bloklash uchun teskari sanoq. */
export function useCooldown() {
  const [left, setLeft] = useState(0);

  useEffect(() => {
    if (left <= 0) return;
    const timer = window.setTimeout(() => setLeft((s) => s - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [left]);

  const start = useCallback((seconds: number) => setLeft(seconds), []);
  return { left, active: left > 0, start };
}

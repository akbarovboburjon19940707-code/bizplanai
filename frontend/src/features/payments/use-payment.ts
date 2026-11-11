"use client";

import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { SLOW_MS, pollDelay } from "./poll";
import type { PaymentEnvelope, PaymentOut } from "./types";

/** /tolov/{id}/ dan id (static export: sahifa bitta `_` nusxadan beriladi, haqiqiy id manzilda). */
export function usePaymentId(): string | null {
  const segment = usePathname()?.split("/").filter(Boolean)[1];
  return segment && segment !== "_" ? decodeURIComponent(segment) : null;
}

/**
 * To'lov holatini kuzatadi. Kechikish har javobdan keyin joriy holatdan qayta hisoblanadi,
 * shuning uchun chek yuklangach (`pending` -> `reviewing`) kuzatish o'zi davom etadi.
 */
export function usePayment(id: string | null) {
  const [data, setData] = useState<PaymentEnvelope | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [tick, setTick] = useState(0);
  const [startedAt] = useState(() => Date.now());
  const manualCheckout = useRef<PaymentEnvelope["checkout"] | null>(null);

  useEffect(() => {
    if (!id) return;
    let active = true;
    apiRequest<PaymentEnvelope>(`/v1/payments/${encodeURIComponent(id)}`)
      .then((res) => {
        if (!active) return;
        // `reviewing` da API checkout bermaydi: karta ma'lumotini oldingi javobdan saqlaymiz
        if ("type" in res.checkout) manualCheckout.current = res.checkout;
        setData(res);
        setError(null);
      })
      .catch((e: unknown) => active && setError(e instanceof ApiError ? e : new ApiError(0, "network_error", "")));
    return () => {
      active = false;
    };
  }, [id, tick]);

  const status = data?.payment.status;
  const provider = data?.payment.provider;
  const retryable = !!error && (error.status === 0 || error.status === 429 || error.status >= 500);
  const delay = status && provider ? pollDelay(status, provider) : retryable ? SLOW_MS : 0;

  useEffect(() => {
    if (!delay) return;
    const timer = window.setTimeout(() => setTick((n) => n + 1), delay);
    return () => window.clearTimeout(timer);
  }, [delay, data, error]);

  const replacePayment = useCallback((payment: PaymentOut) => {
    setData((d) => (d ? { ...d, payment } : d));
  }, []);

  const slow = status === "pending" && provider !== "manual" && Date.now() - startedAt > 120_000;
  return { data, error, slow, savedCheckout: manualCheckout.current, replacePayment };
}

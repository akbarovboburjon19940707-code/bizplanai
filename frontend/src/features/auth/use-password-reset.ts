"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import type { components } from "@/shared/api/schema";

type InitOut = components["schemas"]["PasswordResetInitOut"];
type PollOut = components["schemas"]["PasswordResetPollOut"];

export type ResetState =
  | { phase: "phone" }
  | { phase: "preparing" }
  | { phase: "waiting"; botUrl: string; token: string }
  | { phase: "verified"; token: string }
  | { phase: "mismatch" }
  | { phase: "expired" }
  | { phase: "error"; message: string };

const POLL_MS = 2000;

/**
 * Parolni tiklash (kontrakt 2-bo'lim): init -> botni ochish -> har 2 s poll -> `verified` bo'lsa yangi parol.
 * Telegram login bilan bir xil naqsh: har urinish o'z raqamiga ega, eski poll'lar yangi holatga yozmaydi.
 */
export function usePasswordReset() {
  const [state, setState] = useState<ResetState>({ phase: "phone" });
  const run = useRef(0);

  const reset = useCallback(() => {
    run.current += 1;
    setState({ phase: "phone" });
  }, []);

  useEffect(() => () => void (run.current += 1), []);

  const start = useCallback(async (phone: string) => {
    const id = ++run.current;
    const popup = window.open("about:blank", "_blank"); // popup blokirovkasidan qochish: klik paytida ochiladi
    setState({ phase: "preparing" });
    let init: InitOut;
    try {
      init = await apiRequest<InitOut>("/v1/auth/password-reset/init", {
        method: "POST",
        body: JSON.stringify({ phone }),
      });
    } catch (error) {
      popup?.close();
      if (id === run.current) setState({ phase: "error", message: error instanceof ApiError ? error.message : "" });
      return;
    }
    if (id !== run.current) return popup?.close();
    if (popup) {
      popup.opener = null;
      popup.location.href = init.bot_url;
    }
    setState({ phase: "waiting", botUrl: init.bot_url, token: init.token });

    const deadline = Date.now() + init.expires_in * 1000;
    while (id === run.current) {
      await new Promise((r) => window.setTimeout(r, POLL_MS));
      if (id !== run.current) return;
      if (Date.now() > deadline) return setState({ phase: "expired" });
      try {
        const res = await apiRequest<PollOut>(`/v1/auth/password-reset/poll?token=${encodeURIComponent(init.token)}`);
        if (id !== run.current) return;
        if (res.status === "verified") return setState({ phase: "verified", token: init.token });
        if (res.status === "mismatch") return setState({ phase: "mismatch" });
        if (res.status === "expired") return setState({ phase: "expired" });
      } catch (error) {
        if (error instanceof ApiError && error.status >= 400 && error.status < 500 && error.status !== 429) {
          return setState({ phase: "error", message: error.message });
        }
      }
    }
  }, []);

  return { state, start, reset, setState };
}

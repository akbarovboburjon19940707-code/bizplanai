"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiRequest, startSession } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import type { components } from "@/shared/api/schema";

type InitOut = components["schemas"]["TelegramLoginInitOut"];
type PollOut = components["schemas"]["TelegramLoginPollOut"];

export type TelegramLoginState =
  | { phase: "idle" }
  | { phase: "preparing" }
  | { phase: "waiting"; botUrl: string }
  | { phase: "expired" }
  | { phase: "error"; message: string };

const POLL_MS = 2000;

/**
 * Bot orqali kirish (kontrakt 2-bo'lim): login-init -> botni ochish -> har 2 s login-poll.
 * `authenticated` bo'lsa sessiya boshlanadi; komponent yopilsa yoki bekor qilinsa so'rovlar to'xtaydi.
 */
export function useTelegramLogin() {
  const [state, setState] = useState<TelegramLoginState>({ phase: "idle" });
  const run = useRef(0); // har urinish o'z raqamiga ega: eski poll'lar yangi holatga yozmaydi

  const cancel = useCallback(() => {
    run.current += 1;
    setState({ phase: "idle" });
  }, []);

  useEffect(() => () => void (run.current += 1), []);

  const start = useCallback(async () => {
    const id = ++run.current;
    // Popup blokirovkasidan qochish: oyna klik paytida sinxron ochiladi, manzil keyin beriladi
    const popup = window.open("about:blank", "_blank");
    setState({ phase: "preparing" });
    let init: InitOut;
    try {
      init = await apiRequest<InitOut>("/v1/auth/telegram/login-init", { method: "POST" });
    } catch (error) {
      popup?.close();
      if (id === run.current) {
        setState({ phase: "error", message: error instanceof ApiError ? error.message : "" });
      }
      return;
    }
    if (id !== run.current) return popup?.close();
    if (popup) {
      popup.opener = null;
      popup.location.href = init.bot_url;
    }
    setState({ phase: "waiting", botUrl: init.bot_url });

    const deadline = Date.now() + init.expires_in * 1000;
    while (id === run.current) {
      await new Promise((r) => window.setTimeout(r, POLL_MS));
      if (id !== run.current) return;
      if (Date.now() > deadline) return setState({ phase: "expired" });
      try {
        const res = await apiRequest<PollOut>(
          `/v1/auth/telegram/login-poll?token=${encodeURIComponent(init.token)}`,
        );
        if (id !== run.current) return;
        if (res.status === "authenticated" && res.session) {
          run.current += 1;
          startSession(res.session);
          return;
        }
        if (res.status === "expired") return setState({ phase: "expired" });
      } catch (error) {
        // Tarmoq uzilishi yoki 429: keyingi urinishda davom etadi
        if (error instanceof ApiError && error.status >= 400 && error.status < 500 && error.status !== 429) {
          return setState({ phase: "error", message: error.message });
        }
      }
    }
  }, []);

  return { state, start, cancel };
}

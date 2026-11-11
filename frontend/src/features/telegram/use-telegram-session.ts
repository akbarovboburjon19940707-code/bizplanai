"use client";

import { useCallback, useState } from "react";
import { apiRequest, startSession } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import type { components } from "@/shared/api/schema";
import { markTelegramContext } from "@/shared/lib/download";
import type { TelegramWebApp } from "./telegram-webapp";

type TokenOut = components["schemas"]["TokenOut"];
export type TgState = { phase: "loading" } | { phase: "outside" } | { phase: "error"; message: string } | { phase: "ready" };

/**
 * Mini App ochilganda: SDK yuklangach `initData` bilan kirish (POST /v1/auth/telegram/webapp).
 * Har ochilishda qayta kiriladi: Telegram Web iframe'ida brauzer refresh cookie'ni bloklashi mumkin.
 */
export function useTelegramSession() {
  const [state, setState] = useState<TgState>({ phase: "loading" });

  const init = useCallback(async () => {
    const app: TelegramWebApp | undefined = window.Telegram?.WebApp;
    if (!app?.initData) return setState({ phase: "outside" }); // oddiy brauzerda ochilgan
    app.ready();
    app.expand();
    markTelegramContext(); // keyingi sahifalarda ham yuklash Telegram usulida bo'lsin
    try {
      startSession(await apiRequest<TokenOut>("/v1/auth/telegram/webapp", {
        method: "POST",
        body: JSON.stringify({ init_data: app.initData }),
      }));
      setState({ phase: "ready" });
    } catch (e) {
      setState({ phase: "error", message: e instanceof ApiError ? e.message : "" });
    }
  }, []);

  return { state, init };
}

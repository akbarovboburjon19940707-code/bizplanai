"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import type { components } from "@/shared/api/schema";
import { uz } from "@/messages/uz";

type ChatOut = components["schemas"]["ChatOut"];
export type ProductLink = components["schemas"]["ProductLink"];
export type ChatItem = { role: "user" | "assistant"; content: string; products?: ProductLink[]; handoff?: boolean };

const KEY = "bp_assistant_chat"; // faqat shu tab uchun (sessionStorage); token yoki shaxsiy ma'lumot emas
const MAX_HISTORY = 10;

function load(): ChatItem[] {
  try {
    const raw = window.sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as ChatItem[]).slice(-40) : [];
  } catch {
    return [];
  }
}

/** Suhbat holati: serverga oxirgi 10 xabar (faqat role/content) yuboriladi, ekranda esa butun tarix. */
export function useAssistant() {
  const [items, setItems] = useState<ChatItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loaded = useRef(false);

  useEffect(() => {
    setItems(load());
    loaded.current = true;
  }, []);

  useEffect(() => {
    if (!loaded.current) return;
    try {
      window.sessionStorage.setItem(KEY, JSON.stringify(items.slice(-40)));
    } catch {
      // to'lgan yoki taqiqlangan storage: suhbat faqat xotirada qoladi
    }
  }, [items]);

  const send = useCallback(async (text: string) => {
    const content = text.trim().slice(0, 1000);
    if (!content || busy) return;
    const next = [...items, { role: "user" as const, content }];
    setItems(next);
    setBusy(true);
    setError(null);
    try {
      const history = next.slice(-MAX_HISTORY).map(({ role, content: c }) => ({ role, content: c }));
      while (history.length && history[0].role !== "user") history.shift();
      const res = await apiRequest<ChatOut>("/v1/assistant/chat", { method: "POST", body: JSON.stringify({ messages: history }) });
      setItems((cur) => [...cur, { role: "assistant", content: res.reply, products: res.products, handoff: res.handoff }]);
    } catch (e) {
      setError(e instanceof ApiError && e.message ? e.message : uz.assistant.error);
    } finally {
      setBusy(false);
    }
  }, [items, busy]);

  const reset = useCallback(() => {
    setItems([]);
    setError(null);
  }, []);

  return { items, busy, error, send, reset };
}

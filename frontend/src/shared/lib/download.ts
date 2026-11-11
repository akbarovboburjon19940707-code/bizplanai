"use client";

import type { TelegramWebApp } from "@/features/telegram/telegram-webapp";

/**
 * API bergan imzolangan havoladagi faylni yuklash.
 * Telegram Mini App ichida oddiy `location.href` ishlamaydi (WebView yuklashni qo'llamaydi): u yerda
 * `WebApp.downloadFile` (Bot API 8.0+), bo'lmasa `openLink` (tashqi brauzer) ishlatiladi.
 */
const SDK_URL = "https://telegram.org/js/telegram-web-app.js";
const FLAG = "bp_in_telegram";

/** Mini App ichida ochilganmi (sahifadan sahifaga o'tganda ham eslab qoladi). */
export function markTelegramContext(): void {
  try {
    if (window.TelegramWebviewProxy !== undefined || window.location.hash.includes("tgWebAppData")) {
      window.sessionStorage.setItem(FLAG, "1");
    }
  } catch {
    // sessionStorage yopiq: aniqlash faqat shu sahifada ishlaydi
  }
}

function inTelegram(): boolean {
  if (window.Telegram?.WebApp?.initData) return true;
  if (window.TelegramWebviewProxy !== undefined) return true;
  try {
    return window.sessionStorage.getItem(FLAG) === "1";
  } catch {
    return false;
  }
}

let loading: Promise<TelegramWebApp | null> | null = null;

/** SDK faqat /tg da yuklanadi; boshqa sahifada Telegram ichida bo'lsak yuklash vaqtida yuklaymiz. */
export function telegramWebApp(): Promise<TelegramWebApp | null> {
  if (window.Telegram?.WebApp) return Promise.resolve(window.Telegram.WebApp);
  if (!inTelegram()) return Promise.resolve(null);
  loading ??= new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = SDK_URL;
    script.async = true;
    script.onload = () => resolve(window.Telegram?.WebApp ?? null);
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
  });
  return loading;
}

/** Telegram fayl nomida faqat oddiy belgilar: harf, raqam, bo'sh joy, . _ - */
export function safeFileName(name: string): string {
  const cleaned = name.replace(/[^\p{L}\p{N} ._-]/gu, "").replace(/\s+/g, " ").trim();
  return cleaned.slice(0, 120) || "fayl";
}

export async function openDownload(url: string, fileName: string): Promise<void> {
  const tg = await telegramWebApp();
  if (tg?.downloadFile && (tg.isVersionAtLeast?.("8.0") ?? false)) {
    tg.downloadFile({ url, file_name: safeFileName(fileName) });
    return;
  }
  if (tg?.openLink) {
    tg.openLink(url);
    return;
  }
  window.location.href = url;
}

import { createHash, createHmac, randomInt } from "node:crypto";
import type { Page } from "@playwright/test";

export const API = (process.env.E2E_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
export const BOT_TOKEN = process.env.E2E_TELEGRAM_BOT_TOKEN ?? "123456:TEST";
const WEBHOOK_SECRET = process.env.E2E_TELEGRAM_WEBHOOK_SECRET ?? "e2e+secret/=";
export const ADMIN = {
  phone: process.env.E2E_ADMIN_PHONE ?? "+998901110000",
  password: process.env.E2E_ADMIN_PASSWORD ?? "admin-e2e-pass-123",
  totpSecret: process.env.E2E_ADMIN_TOTP_SECRET ?? "",
};

/** Har test o'z foydalanuvchisi bilan: 9 xonali mahalliy raqam (93 bilan boshlanadi). */
export function newPhone(): string {
  return `93${String(randomInt(0, 10_000_000)).padStart(7, "0")}`;
}

/** RFC 6238 TOTP (SHA1, 30 s, 6 raqam): admin kirishi uchun. */
export function totp(base32: string): string {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  const bits = [...base32.replace(/=+$/, "")].map((c) => alphabet.indexOf(c).toString(2).padStart(5, "0")).join("");
  const key = Buffer.from(bits.match(/.{8}/g)!.map((b) => parseInt(b, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30_000)));
  const h = createHmac("sha1", key).update(counter).digest();
  const o = h[19] & 15;
  return String((h.readUInt32BE(o) & 0x7fffffff) % 1_000_000).padStart(6, "0");
}

export async function api<T = unknown>(path: string, init: RequestInit = {}, token?: string): Promise<{ status: number; body: T }> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API}${path}`, { ...init, headers });
  const text = await res.text();
  return { status: res.status, body: (text ? JSON.parse(text) : undefined) as T };
}

export async function registerViaApi(firstName = "E2E"): Promise<{ phone: string; password: string; token: string }> {
  const phone = newPhone();
  const password = "e2e-pass-12345";
  const r = await api<{ access_token: string }>("/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ phone: `+998${phone}`, password, first_name: firstName }),
  });
  if (r.status !== 201) throw new Error(`register ${r.status}`);
  return { phone, password, token: r.body.access_token };
}

export async function adminToken(): Promise<string> {
  const r = await api<{ access_token: string }>("/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ phone: ADMIN.phone, password: ADMIN.password, totp_code: totp(ADMIN.totpSecret) }),
  });
  if (r.status !== 200) throw new Error(`admin login ${r.status}`);
  return r.body.access_token;
}

/** Bot "Start" bosilishini taqlid qiladi: Telegram webhook'i (backend tokeni sha256 hex kutadi). */
export async function sendBotStart(text: string, from: { id: number; first_name: string; username?: string }) {
  const header = createHash("sha256").update(WEBHOOK_SECRET).digest("hex");
  return fetch(`${API}/v1/telegram/webhook`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": header },
    body: JSON.stringify({ message: { text, chat: { id: from.id }, from } }),
  });
}

/** Botga istalgan xabar (masalan, kontakt): webhook orqali. */
export async function sendBotMessage(message: Record<string, unknown>) {
  const header = createHash("sha256").update(WEBHOOK_SECRET).digest("hex");
  return fetch(`${API}/v1/telegram/webhook`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": header },
    body: JSON.stringify({ message }),
  });
}

/** Telegram'ning rasmiy algoritmi bilan imzolangan Mini App initData. */
export function signedInitData(user: Record<string, unknown>, tamper = false): string {
  const fields: Record<string, string> = { auth_date: String(Math.floor(Date.now() / 1000)), query_id: "AAE2E", user: JSON.stringify(user) };
  const check = Object.keys(fields).sort().map((k) => `${k}=${fields[k]}`).join("\n");
  const secret = createHmac("sha256", "WebAppData").update(BOT_TOKEN).digest();
  let hash = createHmac("sha256", secret).update(check).digest("hex");
  if (tamper) hash = (hash[0] === "a" ? "b" : "a") + hash.slice(1);
  return new URLSearchParams({ ...fields, hash }).toString();
}

/** 1x1 PNG (chek sifatida). */
export const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==", "base64");

export async function login(page: Page, phone: string, password: string) {
  await page.goto("/kirish/");
  await page.getByLabel("Telefon raqam").fill(phone);
  await page.getByLabel("Parol", { exact: true }).fill(password);
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
}

export async function noHorizontalScroll(page: Page): Promise<boolean> {
  return page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
}

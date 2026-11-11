import { expect, test } from "@playwright/test";
import { sendBotStart, signedInitData } from "./helpers";

const sdk = (initData: string) =>
  `window.Telegram={WebApp:{initData:${JSON.stringify(initData)},colorScheme:"light",ready(){window.__tgReady=true},expand(){}}};`;
const tgUser = () => ({ id: 10_000_000 + Math.floor(Math.random() * 1e8), first_name: "Jasur", username: "jasur_e2e" });

test("bot login on the website, then set a first password", async ({ page, context }) => {
  await context.route("https://t.me/**", (r) => r.fulfill({ body: "telegram" }));
  await page.goto("/kirish/");
  await page.getByRole("button", { name: "Telegram orqali kirish" }).click();
  const link = page.getByRole("link", { name: "Telegram’ni ochish" });
  const href = (await link.getAttribute("href"))!;
  expect(href).toMatch(/^https:\/\/t\.me\/[\w_]+\?start=login_/);

  const user = tgUser();
  const hook = await sendBotStart(`/start login_${href.split("login_")[1]}`, user);
  expect(hook.status).toBe(200);
  await expect(page).toHaveURL(/\/kabinet\/$/, { timeout: 15_000 });
  await expect(page.getByText("@jasur_e2e")).toBeVisible();

  await expect(page.getByRole("heading", { name: "Parol o‘rnatish" })).toBeVisible();
  await expect(page.getByLabel("Joriy parol")).toHaveCount(0);
  await page.getByLabel("Yangi parol", { exact: true }).fill("first-pass-123");
  await page.getByLabel("Yangi parolni takrorlang").fill("first-pass-123");
  await page.getByRole("button", { name: "Parol o‘rnatish" }).click();
  await expect(page.getByText("Parol almashtirildi")).toBeVisible();
  await expect(page.getByLabel("Joriy parol")).toBeVisible();
});

test("/tg outside Telegram explains how to open it", async ({ page, context }) => {
  await context.route("https://telegram.org/**", (r) => r.fulfill({ contentType: "application/javascript", body: "" }));
  await page.goto("/tg/");
  await expect(page.getByText("Bu sahifa Telegram ichida ochiladi")).toBeVisible();
  await expect(page.locator("header")).toHaveCount(0);
});

test("/tg signs in with signed initData and keeps the session", async ({ page, context }) => {
  await context.route("https://telegram.org/**", (r) =>
    r.fulfill({ contentType: "application/javascript", body: sdk(signedInitData(tgUser())) }));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/tg/");
  await expect(page.getByRole("heading", { name: "Salom, Jasur!" })).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as { __tgReady?: boolean }).__tgReady)).toBe(true);
  await expect(page.getByText("Tarif va limit")).toBeVisible();
  await page.getByRole("link", { name: /Reja yaratish/ }).click();
  await expect(page).toHaveURL(/\/dashboard\/$/);
  await expect(page.getByRole("link", { name: "Jasur" })).toBeVisible();
});

test("/tg rejects tampered initData", async ({ page, context }) => {
  await context.route("https://telegram.org/**", (r) =>
    r.fulfill({ contentType: "application/javascript", body: sdk(signedInitData(tgUser(), true)) }));
  await page.goto("/tg/");
  await expect(page.getByText("Kirib bo‘lmadi")).toBeVisible();
});

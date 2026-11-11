import { expect, test } from "@playwright/test";
import { login, registerViaApi, sendBotMessage, sendBotStart } from "./helpers";

test("forgot password: confirm the phone in the bot, set a new one and sign in", async ({ page }) => {
  const user = await registerViaApi("Nodira");
  const tg = { id: 700000 + Math.floor(Math.random() * 99999), first_name: "Nodira" };

  await page.goto("/kirish/");
  await page.getByRole("link", { name: "Parolni unutdingizmi?" }).click();
  await expect(page).toHaveURL(/\/parol-tiklash\/$/);
  await page.getByLabel("Telefon raqam").fill(user.phone);
  await page.getByRole("button", { name: "Davom etish" }).click();

  const href = (await page.getByRole("link", { name: "Telegram’ni ochish" }).getAttribute("href"))!;
  expect(href).toMatch(/^https:\/\/t\.me\/[\w_]+\?start=reset_/);
  expect((await sendBotStart(`/start reset_${href.split("reset_")[1]}`, tg)).status).toBe(200);
  const contact = { phone_number: `998${user.phone}`, user_id: tg.id, first_name: "Nodira" };
  expect((await sendBotMessage({ chat: { id: tg.id }, from: tg, contact })).status).toBe(200);

  await expect(page.getByText("Raqam tasdiqlandi")).toBeVisible({ timeout: 15_000 });
  await page.getByLabel("Yangi parol", { exact: true }).fill("tiklangan-parol-1");
  await page.getByLabel("Parolni takrorlang").fill("tiklangan-parol-1");
  await page.getByRole("button", { name: "Parolni saqlash" }).click();
  await expect(page).toHaveURL(/\/kabinet\/$/, { timeout: 15_000 });

  await page.getByRole("button", { name: "Chiqish" }).click();
  await login(page, user.phone, user.password);
  await expect(page.getByText("Telefon raqam yoki parol noto‘g‘ri").or(page.getByText("Telefon raqam yoki parol noto'g'ri"))).toBeVisible();
  await login(page, user.phone, "tiklangan-parol-1");
  await expect(page).toHaveURL(/\/kabinet\/$/);
});

test("forgot password: a different Telegram number is rejected", async ({ page }) => {
  const user = await registerViaApi("Bekzod");
  const tg = { id: 800000 + Math.floor(Math.random() * 99999), first_name: "Bekzod" };
  await page.goto("/parol-tiklash/");
  await page.getByLabel("Telefon raqam").fill(user.phone);
  await page.getByRole("button", { name: "Davom etish" }).click();
  const href = (await page.getByRole("link", { name: "Telegram’ni ochish" }).getAttribute("href"))!;
  await sendBotStart(`/start reset_${href.split("reset_")[1]}`, tg);
  await sendBotMessage({ chat: { id: tg.id }, from: tg, contact: { phone_number: "998977000000", user_id: tg.id } });
  await expect(page.getByText("Telegram raqamingiz kiritilgan raqamga mos kelmadi")).toBeVisible({ timeout: 15_000 });
  await page.getByRole("button", { name: "Qaytadan boshlash" }).click();
  await expect(page.getByLabel("Telefon raqam")).toBeVisible();
});

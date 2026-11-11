import { expect, test } from "@playwright/test";
import { ADMIN, api, adminToken, newPhone, noHorizontalScroll, registerViaApi } from "./helpers";

test("guest sends a contact message; validation, success state and admin inbox", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("contentinfo").getByRole("link", { name: "Aloqa" }).click();
  await expect(page).toHaveURL(/\/aloqa\/$/);
  await expect(page.getByRole("heading", { name: "Aloqa", level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: /\+998 94 721 42 42/ }).first()).toHaveAttribute("href", "tel:+998947214242");

  await page.getByRole("button", { name: "Yuborish" }).click();
  await expect(page.getByText("Ismingizni yozing")).toBeVisible();
  await expect(page.getByText("Xabar kamida 10 belgidan iborat bo‘lsin")).toBeVisible();

  const phone = newPhone();
  const text = `E2E murojaat ${phone}: to'lov qildim, reja ochilmadi.`;
  await page.getByLabel("Ismingiz").fill("Shahzoda");
  await page.getByLabel("Telefon raqamingiz").fill(phone);
  await page.getByLabel("Mavzu").selectOption("payment");
  await page.getByLabel("Xabar", { exact: true }).fill(text);
  await page.getByRole("button", { name: "Yuborish" }).click();
  await expect(page.getByText("Xabaringiz yuborildi")).toBeVisible();

  test.skip(!ADMIN.totpSecret, "E2E_ADMIN_TOTP_SECRET berilmagan");
  const token = await adminToken();
  const inbox = await api<{ message: string; phone: string; topic: string }[]>("/v1/admin/messages?status=new", {}, token);
  const row = inbox.body.find((m) => m.message === text);
  expect(row).toMatchObject({ phone: `+998${phone}`, topic: "payment" });
});

test("signed-in user gets name and phone prefilled; page fits 360 px", async ({ page }) => {
  const user = await registerViaApi("Javohir");
  await page.goto("/kirish/");
  await page.getByLabel("Telefon raqam").fill(user.phone);
  await page.getByLabel("Parol", { exact: true }).fill(user.password);
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await expect(page).toHaveURL(/\/kabinet\/$/);
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/aloqa/");
  await expect(page.getByLabel("Ismingiz")).toHaveValue("Javohir");
  await expect(page.getByLabel("Telefon raqamingiz")).not.toHaveValue("");
  expect(await noHorizontalScroll(page)).toBe(true);
});

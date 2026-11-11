import { expect, test } from "@playwright/test";
import { ADMIN, login, newPhone, noHorizontalScroll, totp } from "./helpers";

test("guest on a protected page goes to sign-in with next", async ({ page }) => {
  await page.goto("/kabinet/");
  await expect(page).toHaveURL(/\/kirish\/\?next=%2Fkabinet%2F$/);
});

test("register, keep session on reload, edit profile, change password, sign out and in", async ({ page }) => {
  const phone = newPhone();
  await page.goto("/royxat/");
  await page.getByLabel("Telefon raqam").fill("90 12");
  await page.getByLabel("Parol", { exact: true }).fill("short");
  await page.getByLabel("Parolni takrorlang").fill("other");
  await page.getByRole("button", { name: "Ro‘yxatdan o‘tish" }).last().click();
  await expect(page.getByText("Telefon raqamni to‘liq kiriting (9 ta raqam)")).toBeVisible();
  await expect(page.getByText("Parol kamida 8 belgidan iborat bo‘lsin").first()).toBeVisible();
  await expect(page.getByText("Parollar bir xil emas")).toBeVisible();

  await page.getByLabel("Telefon raqam").fill(`+998${phone}`);
  await expect(page.getByLabel("Telefon raqam")).toHaveValue(`${phone.slice(0, 2)} ${phone.slice(2, 5)} ${phone.slice(5, 7)} ${phone.slice(7)}`);
  await page.getByLabel("Ismingiz").fill("Aziz");
  await page.getByLabel("Parol", { exact: true }).fill("secret-pass-1");
  await page.getByLabel("Parolni takrorlang").fill("secret-pass-1");
  await page.getByRole("button", { name: "Ro‘yxatdan o‘tish" }).last().click();
  await expect(page).toHaveURL(/\/kabinet\/$/);
  await expect(page.getByRole("heading", { name: "Salom, Aziz!" })).toBeVisible();
  await expect(page.getByText("Hali reja yaratilmagan.")).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Salom, Aziz!" })).toBeVisible();

  await page.getByLabel("Ism", { exact: true }).fill("Azizbek");
  await page.getByLabel("Email").fill("aziz@example.com");
  await page.getByRole("button", { name: "Saqlash" }).click();
  await expect(page.getByText("Saqlandi")).toBeVisible();
  await expect(page.getByRole("link", { name: "Azizbek" })).toBeVisible();
  await page.getByLabel("Email").fill("");
  await page.getByRole("button", { name: "Saqlash" }).click();
  await page.reload();
  await expect(page.getByLabel("Email")).toHaveValue("");

  await page.getByLabel("Joriy parol").fill("wrong-pass-0");
  await page.getByLabel("Yangi parol", { exact: true }).fill("new-pass-12345");
  await page.getByLabel("Yangi parolni takrorlang").fill("new-pass-12345");
  await page.getByRole("button", { name: "Parolni almashtirish" }).click();
  await expect(page.getByText("Joriy parol noto'g'ri")).toBeVisible();
  await page.getByLabel("Joriy parol").fill("secret-pass-1");
  await page.getByRole("button", { name: "Parolni almashtirish" }).click();
  await expect(page.getByText("Parol almashtirildi")).toBeVisible();

  await page.getByRole("button", { name: "Chiqish" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("link", { name: "Kirish" })).toBeVisible();

  await page.goto("/kirish/?next=%2Fdashboard%2F");
  await page.getByLabel("Telefon raqam").fill(phone);
  await page.getByLabel("Parol", { exact: true }).fill("secret-pass-1");
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await expect(page.getByText("Telefon raqam yoki parol noto'g'ri")).toBeVisible();
  await page.getByLabel("Parol", { exact: true }).fill("new-pass-12345");
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await expect(page).toHaveURL(/\/dashboard\/$/);

  await page.goto("/kirish/");
  await expect(page).toHaveURL(/\/kabinet\/$/);
});

test("duplicate phone links to sign-in; open redirect is ignored", async ({ page }) => {
  const phone = newPhone();
  await page.goto("/royxat/");
  for (let i = 0; i < 2; i++) {
    if (i) {
      await page.getByRole("button", { name: "Chiqish" }).click();
      await page.goto("/royxat/");
    }
    await page.getByLabel("Telefon raqam").fill(phone);
    await page.getByLabel("Parol", { exact: true }).fill("dup-pass-123");
    await page.getByLabel("Parolni takrorlang").fill("dup-pass-123");
    await page.getByRole("button", { name: "Ro‘yxatdan o‘tish" }).last().click();
    if (!i) await expect(page).toHaveURL(/\/kabinet\/$/);
  }
  await expect(page.getByText("Bu raqam allaqachon ro‘yxatdan o‘tgan.")).toBeVisible();
  await expect(page.getByRole("link", { name: /Kirish sahifasiga/ })).toBeVisible();

  await page.goto("/kirish/?next=%2F%2Fevil.example");
  await page.getByLabel("Telefon raqam").fill(phone);
  await page.getByLabel("Parol", { exact: true }).fill("dup-pass-123");
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await expect(page).toHaveURL(/^http:\/\/localhost:\d+\/kabinet\/$/);
});

test("admin sign-in requires a valid TOTP code", async ({ page }) => {
  test.skip(!ADMIN.totpSecret, "E2E_ADMIN_TOTP_SECRET berilmagan");
  await login(page, ADMIN.phone.replace("+998", ""), ADMIN.password);
  await expect(page.getByLabel("Tasdiqlash kodi")).toBeFocused();
  await page.getByLabel("Tasdiqlash kodi").fill("000000");
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await expect(page.getByText("Kod noto'g'ri yoki eskirgan")).toBeVisible();
  await page.getByLabel("Tasdiqlash kodi").fill(totp(ADMIN.totpSecret));
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await expect(page).toHaveURL(/\/kabinet\/$/);
});

test("auth pages fit a 360 px screen", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 780 });
  for (const path of ["/kirish/", "/royxat/"]) {
    await page.goto(path);
    await expect(page.getByLabel("Telefon raqam")).toBeVisible();
    expect(await noHorizontalScroll(page)).toBe(true);
  }
});

import { expect, test } from "@playwright/test";
import { ADMIN, PNG, adminToken, api, newPhone, noHorizontalScroll } from "./helpers";

const PRODUCT = "/katalog/qoy-sotib-olish-biznes-rejasi/";

test("catalog: totals, category filter, search, empty state, pagination in the URL", async ({ page }) => {
  await page.goto("/katalog/");
  await expect(page.getByText("269 ta reja topildi")).toBeVisible();
  await expect(page.locator("article")).toHaveCount(24);
  await page.getByRole("button", { name: /Transport/ }).click();
  await expect(page).toHaveURL(/category=transport/);
  await expect(page.getByText("9 ta reja topildi")).toBeVisible();
  await page.getByRole("button", { name: /Barchasi/ }).click();
  await page.getByLabel("Qidirish").fill("novvoy");
  await expect(page).toHaveURL(/q=novvoy/);
  await expect(page.getByText(/^\d+ ta reja topildi$/)).not.toHaveText("269 ta reja topildi");
  await page.getByLabel("Qidirish").fill("zzqqxx");
  await expect(page.getByText("Hech narsa topilmadi")).toBeVisible();
  await page.getByRole("button", { name: "Filtrni tozalash" }).click();
  await expect(page.getByText("269 ta reja topildi")).toBeVisible();
  await page.getByRole("button", { name: "Keyingi" }).click();
  await expect(page).toHaveURL(/page=2/);
  await page.reload();
  await expect(page.getByText("2 / 12")).toBeVisible();
});

test("guest buys a plan by card: register, receipt, admin approval, owned on reload", async ({ page }) => {
  test.skip(!ADMIN.totpSecret, "E2E_ADMIN_TOTP_SECRET berilmagan");
  await page.goto(PRODUCT);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Qo'y");
  await page.getByRole("button", { name: "Sotib olish uchun kiring" }).click();
  await expect(page).toHaveURL(/\/kirish\/\?next=%2Fkatalog%2Fqoy-sotib-olish-biznes-rejasi%2F/);
  await page.getByRole("link", { name: "Ro‘yxatdan o‘ting" }).click();
  await expect(page).toHaveURL(/\/royxat\//);
  await page.getByLabel("Telefon raqam").fill(newPhone());
  await page.getByLabel("Parol", { exact: true }).fill("buyer-pass-123");
  await page.getByLabel("Parolni takrorlang").fill("buyer-pass-123");
  await page.getByRole("button", { name: "Ro‘yxatdan o‘tish" }).last().click();
  await expect(page).toHaveURL(new RegExp(`${PRODUCT}$`));

  await page.getByRole("button", { name: "Sotib olish", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "To‘lov usulini tanlang" });
  await expect(dialog.getByRole("button", { name: /Karta orqali/ })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await page.getByRole("button", { name: "Sotib olish", exact: true }).click();
  await dialog.getByRole("button", { name: /Karta orqali/ }).click();
  await expect(page).toHaveURL(/\/tolov\/cat_[^/]+\/?$/);
  const paymentId = page.url().split("/tolov/")[1].replace(/\/$/, "");

  await page.setInputFiles("#receipt", { name: "notes.txt", mimeType: "text/plain", buffer: Buffer.from("x") });
  await expect(page.getByText("Faqat JPG, PNG, WEBP yoki PDF fayl yuklang")).toBeVisible();
  await page.setInputFiles("#receipt", { name: "chek.png", mimeType: "image/png", buffer: PNG });
  await page.getByRole("button", { name: "Chekni yuborish" }).click();
  await expect(page.getByText("Chek tekshirilmoqda")).toBeVisible();

  const approved = await api(`/v1/admin/payments/${paymentId}/approve`, { method: "POST", body: "{}" }, await adminToken());
  expect(approved.status).toBe(200);
  await expect(page.getByText("To‘lov qabul qilindi")).toBeVisible({ timeout: 30_000 });
  // CI rejaning namunaviy PDF'ini qo'yadi (fayli yo'q reja sotilmaydi): yuklash to'liq tugashini kutamiz,
  // aks holda keyingi page.goto davom etayotgan yuklashni uzib, ERR_ABORTED beradi
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "PDF’ni yuklab olish" }).click();
  expect((await download).suggestedFilename()).toMatch(/\.pdf$/);

  await page.goto(PRODUCT);
  await expect(page.getByText("Bu reja sizda bor.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Sotib olish", exact: true })).toHaveCount(0);
});

test("tariffs from the API: subscription and single plan by card", async ({ page }) => {
  await page.goto("/royxat/");
  await page.getByLabel("Telefon raqam").fill(newPhone());
  await page.getByLabel("Parol", { exact: true }).fill("tariff-pass-123");
  await page.getByLabel("Parolni takrorlang").fill("tariff-pass-123");
  await page.getByRole("button", { name: "Ro‘yxatdan o‘tish" }).last().click();
  await expect(page).toHaveURL(/\/kabinet\/$/);

  await page.goto("/tariflar/");
  await expect(page.getByRole("article")).toHaveCount(3);
  await expect(page.getByRole("article", { name: "Bepul" }).getByText("Joriy tarif")).toBeVisible();
  await page.getByRole("article", { name: "Standart" }).getByRole("button", { name: "Tanlash" }).click();
  await page.getByRole("dialog").getByRole("button", { name: /Karta orqali/ }).click();
  await expect(page).toHaveURL(/\/tolov\/sub_/);
  await expect(page.locator("p.text-2xl")).toHaveText("200 000 so‘m"); // Standart (2026-11-12)

  await page.goto("/tariflar/");
  await expect(page.getByRole("heading", { name: "Bitta reja" })).toBeVisible();
  // Narxlar statik HTML'da (SEO): tugma React ulanishidan oldin ko'rinadi. "Joriy tarif" belgisi /v1/me dan keladi,
  // ya'ni sahifa jonlangan: shundan keyin bosamiz (aks holda bosish yo'qolishi mumkin)
  await expect(page.getByRole("article", { name: "Bepul" }).getByText("Joriy tarif")).toBeVisible();
  await page.getByRole("button", { name: "Sotib olish" }).click();
  await page.getByRole("dialog").getByRole("button", { name: /Karta orqali/ }).click();
  await expect(page).toHaveURL(/\/tolov\/crd_/);

  await page.goto("/kabinet/");
  await expect(page.getByText("Kutilmoqda").first()).toBeVisible();
  await page.goto("/tolov/does-not-exist/");
  await expect(page.getByText(/topilmadi/i)).toBeVisible();
});

test("catalog pages fit a 360 px screen", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 780 });
  for (const path of ["/katalog/", "/tariflar/", PRODUCT]) {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    expect(await noHorizontalScroll(page)).toBe(true);
  }
});

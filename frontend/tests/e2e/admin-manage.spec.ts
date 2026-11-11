import { expect, test, type Page } from "@playwright/test";
import { ADMIN, api, registerViaApi, totp } from "./helpers";

test.skip(!ADMIN.totpSecret, "E2E_ADMIN_TOTP_SECRET berilmagan");

async function adminLogin(page: Page, next: string) {
  await page.goto(`/kirish/?next=${encodeURIComponent(next)}`);
  await page.getByLabel("Telefon raqam").fill(ADMIN.phone.replace("+998", ""));
  await page.getByLabel("Parol", { exact: true }).fill(ADMIN.password);
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await page.getByLabel("Tasdiqlash kodi").fill(totp(ADMIN.totpSecret));
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await expect(page).toHaveURL(new RegExp(next.replace(/\//g, "\\/") + "$"));
}

const PDF = Buffer.from("%PDF-1.4\n" + "0".repeat(1500));

test("admin adds a catalog plan with a PDF, it goes live, then deletes it", async ({ page }) => {
  await adminLogin(page, "/admin/katalog/");
  await page.getByRole("button", { name: "+ Yangi reja qo‘shish" }).click();
  const dialog = page.getByRole("dialog");
  const title = `E2E Kurka fermasi ${Date.now()}`;
  await dialog.getByLabel("Nomi").fill(title);
  await dialog.getByLabel("Narx (so‘m)").fill("45000");
  await dialog.getByRole("button", { name: "Qo‘shish" }).click();
  await expect(dialog.getByText("PDF faylni tanlang")).toBeVisible(); // PDF majburiy
  await dialog.getByLabel(/PDF fayl/).setInputFiles({ name: "reja.pdf", mimeType: "application/pdf", buffer: PDF });
  await dialog.getByRole("button", { name: "Qo‘shish" }).click();
  await expect(page.getByText("Reja qo‘shildi")).toBeVisible();

  const row = page.locator("li", { hasText: title });
  await expect(row).toContainText("PDF 1 KB");
  await expect(row.getByText("Yashirilgan")).toHaveCount(0); // darhol faol
  const id = (await row.locator(".font-mono").textContent())!.trim();
  expect((await api<{ price_som: number }>(`/v1/catalog/products/${id}`)).body.price_som).toBe(45000);

  await row.getByRole("button", { name: "O‘chirish" }).click();
  await row.getByRole("button", { name: "Ha, o‘chirish" }).click();
  await expect(page.getByText("O‘chirildi")).toBeVisible();
  await expect(page.locator("li", { hasText: title })).toHaveCount(0);
  expect((await api(`/v1/catalog/products/${id}`)).status).toBe(404);
});

test("admin gives a user the Standart tariff for 7 days and 2 credits, then revokes the tariff", async ({ page }) => {
  const user = await registerViaApi("Nigora");
  await adminLogin(page, "/admin/foydalanuvchilar/");
  await page.getByPlaceholder(/Telefon, ism/).fill(user.phone);
  await expect(page.locator("tbody tr")).toHaveCount(1); // qidiruv (debounce) natijasi: faqat shu foydalanuvchi
  const row = page.locator("tbody tr", { hasText: "Nigora" });
  await row.getByRole("button", { name: "Tarif" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByText("Obuna yo‘q (bepul tarif)")).toBeVisible();

  await dialog.getByLabel("Izoh (ixtiyoriy)").fill("Sinov uchun");
  await dialog.getByLabel("Tarif", { exact: true }).selectOption({ label: "Standart" });
  await dialog.getByLabel("Kunlar").fill("7");
  await dialog.locator("form").filter({ hasText: "Tarif berish" }).getByRole("button", { name: "Berish" }).click();
  await expect(dialog.getByText("Bajarildi")).toBeVisible();
  await expect(dialog.getByText("faol")).toBeVisible();

  await dialog.getByLabel("Soni (1–20)").fill("2");
  await dialog.locator("form").filter({ hasText: "Kredit berish" }).getByRole("button", { name: "Berish" }).click();
  await expect(dialog.getByText("Kreditlar (bitta reja): 2")).toBeVisible();

  const me = await api<{ subscription: { tariff_code: string }; user: { plan_credits: number } }>("/v1/me", {}, user.token);
  expect(me.body.subscription.tariff_code).toBe("pro");
  expect(me.body.user.plan_credits).toBe(2);

  page.once("dialog", (d) => void d.accept());
  await dialog.getByRole("button", { name: "Bekor qilish" }).first().click();
  await expect(dialog.getByText("bekor qilingan").first()).toBeVisible();
  const after = await api<{ subscription: { tariff_code: string } }>("/v1/me", {}, user.token);
  expect(after.body.subscription.tariff_code).toBe("basic");
});

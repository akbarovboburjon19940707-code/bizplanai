import { expect, test } from "@playwright/test";
import { ADMIN, PNG, api, login, registerViaApi, totp } from "./helpers";

test.skip(!ADMIN.totpSecret, "E2E_ADMIN_TOTP_SECRET berilmagan");

async function paymentWithReceipt(token: string, body: object): Promise<string> {
  const p = await api<{ payment: { id: string } }>("/v1/payments", { method: "POST", body: JSON.stringify(body) }, token);
  const fd = new FormData();
  fd.append("file", new Blob([PNG], { type: "image/png" }), "chek.png");
  await api(`/v1/payments/${p.body.payment.id}/receipt`, { method: "POST", body: fd }, token);
  return p.body.payment.id;
}

test("regular users get a 404 view; admins review receipts, approve and reject", async ({ page, context }) => {
  const customer = await registerViaApi("Dilnoza");
  const approveId = await paymentWithReceipt(customer.token, { kind: "plan_credit", provider: "manual" });
  const rejectId = await paymentWithReceipt(customer.token, { kind: "subscription", target_id: "pro", provider: "manual" });

  await login(page, customer.phone, customer.password);
  await expect(page).toHaveURL(/\/kabinet\/$/);
  await expect(page.getByRole("link", { name: "Admin panel" })).toHaveCount(0);
  await page.goto("/admin/tolovlar/");
  await expect(page.getByText("Sahifa topilmadi")).toBeVisible();
  await page.getByRole("button", { name: "Chiqish" }).click();
  await expect(page).toHaveURL(/\/$/);

  await page.goto("/admin/tolovlar/");
  await expect(page).toHaveURL(/\/kirish\/\?next=%2Fadmin%2Ftolovlar%2F/);
  await page.getByLabel("Telefon raqam").fill(ADMIN.phone.replace("+998", ""));
  await page.getByLabel("Parol", { exact: true }).fill(ADMIN.password);
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await page.getByLabel("Tasdiqlash kodi").fill(totp(ADMIN.totpSecret));
  await page.locator("form").getByRole("button", { name: "Kirish" }).click();
  await expect(page).toHaveURL(/\/admin\/tolovlar\/$/);

  const row = page.locator("li", { hasText: approveId });
  await expect(row).toContainText("Dilnoza");
  const tabPromise = context.waitForEvent("page");
  await row.getByRole("button", { name: "Chekni ko‘rish" }).click();
  const tab = await tabPromise;
  await tab.waitForURL(/\/v1\/files\/|r2\.cloudflarestorage/);
  await tab.close();

  await row.getByRole("button", { name: "Tasdiqlash" }).click();
  await page.getByRole("dialog").getByLabel("Izoh (ixtiyoriy)").fill("chek to'g'ri");
  await page.getByRole("dialog").getByRole("button", { name: "Tasdiqlash" }).click();
  await expect(page.getByText("Tasdiqlandi")).toBeVisible();
  await expect(page.locator("li", { hasText: approveId })).toHaveCount(0);
  const me = await api<{ user: { plan_credits: number } }>("/v1/me", {}, customer.token);
  expect(me.body.user.plan_credits).toBe(1);

  await page.locator("li", { hasText: rejectId }).getByRole("button", { name: "Rad etish" }).click();
  await page.getByRole("dialog").getByLabel(/Rad etish sababi/).fill("Summa mos emas");
  await page.getByRole("dialog").getByRole("button", { name: "Rad etish" }).click();
  await expect(page.getByText("Rad etildi")).toBeVisible();
  const rejected = await api<{ payment: { status: string; admin_note: string } }>(`/v1/payments/${rejectId}`, {}, customer.token);
  expect(rejected.body.payment).toMatchObject({ status: "rejected", admin_note: "Summa mos emas" });

  const adminNav = page.getByRole("navigation", { name: "Admin panel" });
  await adminNav.getByRole("link", { name: "Statistika" }).click();
  await expect(page.locator("p.text-2xl")).toHaveCount(9); // 9-karta: yangi murojaatlar

  await adminNav.getByRole("link", { name: "Foydalanuvchilar" }).click();
  await page.getByPlaceholder(/Telefon, ism/).fill(customer.phone);
  await expect(page.locator("tbody tr")).toHaveCount(1);

  await adminNav.getByRole("link", { name: "Katalog" }).click();
  await page.getByPlaceholder("Nomi, ID yoki slug").fill("qoy-sotib-olish");
  await expect(page.getByText("Jami: 1")).toBeVisible();
  const product = page.locator("li").first();
  const original = await product.getByLabel("Narx (so‘m)").inputValue();
  await product.getByLabel("Narx (so‘m)").fill("45000");
  await expect(product.getByLabel("Narx (so‘m)")).toHaveValue("45 000");
  await product.getByRole("button", { name: "Saqlash" }).click();
  await expect(product.getByText("Saqlandi")).toBeVisible();
  expect((await api<{ price_som: number }>("/v1/catalog/products/qoy-sotib-olish-biznes-rejasi")).body.price_som).toBe(45000);
  await product.getByRole("button", { name: "Yashirish" }).click();
  await expect(product.getByText("Yashirilgan", { exact: true })).toBeVisible();
  expect((await api("/v1/catalog/products/qoy-sotib-olish-biznes-rejasi")).status).toBe(404);
  await product.getByRole("button", { name: "Ko‘rsatish" }).click();
  await expect(product.getByRole("button", { name: "Yashirish" })).toBeVisible();
  await product.getByLabel("Narx (so‘m)").fill(original);
  await product.getByRole("button", { name: "Saqlash" }).click();
  await expect(product.getByText("Saqlandi")).toBeVisible();
  expect((await api("/v1/catalog/products/qoy-sotib-olish-biznes-rejasi")).status).toBe(200);
});

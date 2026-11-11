import { expect, test } from "@playwright/test";
import { login, registerViaApi } from "./helpers";

const DRAFT = {
  faoliyat_turi: "ishlab_chiqarish", loyiha_nomi: "Non sexi", soliq_turi: "ytt", loyiha_qiymati: 300000000,
  oz_mablag: 100000000, kredit: 200000000, kredit_turi: "differensial", foiz: 18, muddat: 36, imtiyoz: 6,
  mahsulotlar: [{ nomi: "Non", hajm: 400000, narx: 3000, olchov: "dona" }], direktor: 1, rahbar_oylik: 5000000,
  xodim: 4, ishchi_oylik: 3000000, quvvat: [75, 77, 80, 82, 85, 90, 92, 95, 100, 100], diskont: 14, use_ai: false,
  rasm_turi: "yoq",
};

test("free user sees results for free, but documents require payment", async ({ page }) => {
  const user = await registerViaApi("Dilshod");
  await login(page, user.phone, user.password);
  await expect(page).toHaveURL(/\/kabinet\/$/);
  await expect(page.getByText(/Bepul tarifda hisob-kitoblar ekranda ko‘rinadi/)).toBeVisible();

  await page.addInitScript((d) => sessionStorage.setItem("bp_plan_draft", JSON.stringify(d)), DRAFT);
  await page.goto("/dashboard/");
  for (let i = 0; i < 4; i++) await page.getByRole("button", { name: "Keyingi" }).click();
  await expect(page.locator("aside").getByText("NPV (3 yil)")).toBeVisible(); // hisob-kitob bepul ko'rinadi
  await expect(page.getByRole("heading", { name: "Hisob-kitob tayyor" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Rejani yaratish" })).toHaveCount(0);

  await page.getByRole("button", { name: /Bitta reja: 50 000/ }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByText("Bitta biznes-reja (Word va Excel, AI matn bilan)")).toBeVisible();
  await expect(dialog.getByRole("button", { name: /Karta orqali o‘tkazma/ })).toBeVisible();
});

test("tariffs page explains the free plan has no documents", async ({ page }) => {
  await page.goto("/tariflar/");
  const free = page.getByRole("article", { name: "Bepul" });
  await expect(free.getByText("Hisob-kitoblar ekranda: NPV, IRR, jadvallar")).toBeVisible();
  await expect(free.getByText("Word va Excel hujjatlar (to‘lov bilan)")).toBeVisible();
  await expect(page.getByRole("article", { name: "Standart" }).getByText("Oyiga 10 ta reja")).toBeVisible();
  await expect(page.getByRole("article", { name: "Premium" }).getByText("Oyiga 100 ta reja")).toBeVisible();
});

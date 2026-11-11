import { expect, test } from "@playwright/test";
import { noHorizontalScroll } from "./helpers";

// E2E backend'da AI o'chiq: yordamchi zaxira javob beradi, katalog qidiruvi esa AI'siz ishlaydi
test("chat widget: suggestion, catalog cards, contact handoff, history survives reload", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Savol berish" }).click();
  const dialog = page.getByRole("dialog", { name: "BizplanAI yordamchisi" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Baliqchilik bo‘yicha tayyor reja bormi?" }).click();
  await expect(dialog.getByText("Mos tayyor rejalar")).toBeVisible();
  await expect(dialog.getByRole("link", { name: /baliq/i }).first()).toHaveAttribute("href", /\/katalog\/.+\/$/);
  await expect(dialog.getByRole("link", { name: "Aloqa sahifasiga o‘tish →" })).toBeVisible();

  await dialog.getByLabel("Savolingizni yozing…").fill("Tariflar qancha?");
  await dialog.getByLabel("Savolingizni yozing…").press("Enter");
  await expect(dialog.getByText("Tariflar qancha?")).toBeVisible();
  await expect(dialog.getByRole("link", { name: "Aloqa sahifasiga o‘tish →" })).toHaveCount(2);

  await page.reload();
  await page.getByRole("button", { name: "Savol berish" }).click();
  await expect(page.getByRole("dialog").getByText("Tariflar qancha?")).toBeVisible();
  await page.getByRole("button", { name: "Yangi suhbat" }).click();
  await expect(page.getByRole("dialog").getByText("Tariflar qancha?")).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("chat widget fits a phone screen and is hidden in the Mini App", async ({ page, context }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await page.goto("/aloqa/");
  await page.getByRole("button", { name: "Savol berish" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(await noHorizontalScroll(page)).toBe(true);
  // Mini App'da yordamchi bot o'zida; /admin/ ni mehmon ochsa /kirish/ ga yo'naltiriladi (u yerda chat bor), shuning
  // uchun admin holati bu yerda emas, yo'naltirishsiz /tg/ da tekshiriladi
  await context.route("https://telegram.org/**", (r) => r.fulfill({ contentType: "application/javascript", body: "" }));
  await page.goto("/tg/");
  await expect(page.getByText("Bu sahifa Telegram ichida ochiladi")).toBeVisible();
  await expect(page.getByRole("button", { name: "Savol berish" })).toHaveCount(0);
});

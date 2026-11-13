import { expect, test } from "@playwright/test";
import { noHorizontalScroll } from "./helpers";

test("landing shows API data in static HTML, with SEO tags", async ({ page, request, baseURL }) => {
  await page.goto("/");
  await expect(page.locator("section[aria-labelledby=popular] article")).toHaveCount(4);
  await expect(page.getByRole("heading", { name: /3 qadam/ })).toBeVisible();
  await expect(page.getByText("Hisob-kitob har doim bepul").first()).toBeVisible(); // bepul: faqat hisob-kitob
  await expect(page.getByRole("heading", { name: /3 daqiqada/ })).toBeVisible();
  const html = await (await request.get(baseURL!)).text();
  expect(html).toContain("Sohangiz bo‘yicha tayyor biznes-reja");
  expect(html).toContain("269 ta tayyor reja"); // rejalar soni build vaqtida API'dan
  expect(html).toContain('"@type":"FAQPage"');
  expect(html).not.toContain("formulali"); // Excel'da formula yo'q: bunday va'da bo'lmasin
  expect(html).toMatch(/property="og:title"/);
  expect(html).toMatch(/rel="canonical"/);
  await page.setViewportSize({ width: 360, height: 780 });
  expect(await noHorizontalScroll(page)).toBe(true);
});

test("sitemap lists every catalog plan; robots hides private pages", async ({ request }) => {
  const sitemap = await (await request.get("/sitemap.xml")).text();
  expect(sitemap.match(/<url>/g)?.length).toBe(4 + 269);
  expect(sitemap).not.toContain("/dashboard/"); // kirish talab qiladigan ish sahifasi
  const robots = await (await request.get("/robots.txt")).text();
  for (const path of ["/admin/", "/kabinet/", "/tolov/", "/tg/"]) expect(robots).toContain(`Disallow: ${path}`);
});

test("each public page declares its own canonical URL", async ({ request }) => {
  const canonical = async (path: string) => (await (await request.get(path)).text()).match(/<link rel="canonical" href="([^"]+)"/)?.[1] ?? null;
  expect(await canonical("/")).toMatch(/\/$/);
  expect(await canonical("/katalog/")).toMatch(/\/katalog\/$/);
  expect(await canonical("/tariflar/")).toMatch(/\/tariflar\/$/);
  expect(await canonical("/katalog/qoy-sotib-olish-biznes-rejasi/")).toMatch(/\/katalog\/qoy-sotib-olish-biznes-rejasi\/$/);
  expect(await canonical("/kirish/")).toBeNull(); // shaxsiy sahifa: canonical yo'q (va noindex)
});

test("prices, catalog list and product data are in static HTML (no JS needed)", async ({ request }) => {
  const tariffs = await (await request.get("/tariflar/")).text();
  expect(tariffs).toContain("200 000");
  const catalog = await (await request.get("/katalog/")).text();
  expect(new Set(catalog.match(/href="\/katalog\/[a-z0-9-]+\/"/g)).size).toBe(24);
  const product = await (await request.get("/katalog/qoy-sotib-olish-biznes-rejasi/")).text();
  const ld = product.match(/<script type="application\/ld\+json">(.*?)<\/script>/)?.[1];
  expect(JSON.parse(ld!)).toMatchObject({ "@type": "Product", offers: { priceCurrency: "UZS" } });
  expect(product).toMatch(/property="og:image" content="[^"]+\/thumb\?v=/);
});

test("a guest visit does not hit /v1/auth/refresh (no 401 noise); the font is applied", async ({ page }) => {
  const refreshCalls: string[] = [];
  page.on("request", (r) => { if (r.url().includes("/v1/auth/refresh")) refreshCalls.push(r.url()); });
  await page.goto("/"); // birinchi tashrif: belgi joriy qilinishidan oldingi sessiya uchun bitta tekshiruv
  await page.waitForLoadState("networkidle");
  refreshCalls.length = 0;
  await page.goto("/katalog/");
  await page.waitForLoadState("networkidle");
  expect(refreshCalls).toEqual([]);
  const font = await page.evaluate(() => getComputedStyle(document.body).fontFamily);
  expect(font).not.toMatch(/^"?Times/);
  expect(font.toLowerCase()).toContain("inter");
});

test("footer: share links point to the current public page, socials have labels", async ({ page }) => {
  await page.goto("/tariflar/");
  const footer = page.locator("footer");
  const tg = await footer.getByRole("link", { name: "Telegram", exact: true }).getAttribute("href");
  expect(tg).toMatch(/^https:\/\/t\.me\/share\/url\?url=.*%2Ftariflar%2F/);
  const fb = await footer.getByRole("link", { name: "Facebook" }).getAttribute("href");
  expect(fb).toMatch(/^https:\/\/www\.facebook\.com\/sharer\/sharer\.php\?u=.*%2Ftariflar%2F/);
  for (const name of ["Telegram kanal", "Instagram", "YouTube"]) await expect(footer.getByRole("link", { name })).toBeVisible();
  await expect(footer.getByText("Du–Sh, 9:00–19:00")).toBeVisible();
  await expect(footer.getByRole("button", { name: "Ulashish" })).toBeVisible();
});

test("home: FAQ opens, header link jumps to it, prices come from the API", async ({ page }) => {
  await page.goto("/");
  const pricing = page.locator("section[aria-labelledby=pricing]");
  await expect(pricing.getByText("200 000")).toBeVisible();
  await expect(pricing.getByText("Eng ommabop")).toBeVisible();
  const q = page.getByText("Ro‘yxatdan o‘tish shartmi?");
  await q.click();
  await expect(page.getByText(/Rejani saqlash va Word\/Excel hujjatni olish uchun/)).toBeVisible();
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.getByRole("link", { name: "Savollar" }).click();
  await expect(page).toHaveURL(/#savollar$/);
});

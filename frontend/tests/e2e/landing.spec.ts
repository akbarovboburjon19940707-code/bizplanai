import { expect, test } from "@playwright/test";
import { noHorizontalScroll } from "./helpers";

test("landing shows API data in static HTML, with SEO tags", async ({ page, request, baseURL }) => {
  await page.goto("/");
  await expect(page.locator("article")).toHaveCount(6);
  await expect(page.getByText("3 bosqichda tayyor")).toBeVisible();
  await expect(page.getByText("Hisob-kitoblarni bepul ko‘ring").first()).toBeVisible(); // bepul: faqat hisob-kitob
  const html = await (await request.get(baseURL!)).text();
  expect(html).toContain("Mashhur tayyor rejalar");
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

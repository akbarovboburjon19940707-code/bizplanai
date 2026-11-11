import { expect, test } from "@playwright/test";
import { noHorizontalScroll } from "./helpers";

test("landing shows API data in static HTML, with SEO tags", async ({ page, request, baseURL }) => {
  await page.goto("/");
  await expect(page.locator("article")).toHaveCount(6);
  await expect(page.getByText("3 bosqichda tayyor")).toBeVisible();
  await expect(page.getByText("Kuniga 3 ta reja").first()).toBeVisible();
  const html = await (await request.get(baseURL!)).text();
  expect(html).toContain("Mashhur tayyor rejalar");
  expect(html).toMatch(/property="og:title"/);
  expect(html).toMatch(/rel="canonical"/);
  await page.setViewportSize({ width: 360, height: 780 });
  expect(await noHorizontalScroll(page)).toBe(true);
});

test("sitemap lists every catalog plan; robots hides private pages", async ({ request }) => {
  const sitemap = await (await request.get("/sitemap.xml")).text();
  expect(sitemap.match(/<url>/g)?.length).toBe(5 + 269);
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

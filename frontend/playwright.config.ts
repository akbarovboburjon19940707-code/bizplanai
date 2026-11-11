import { defineConfig, devices } from "@playwright/test";

/**
 * E2E: haqiqiy backend (E2E_API_URL) va shu API'ga qarshi build qilingan statik sayt (E2E_WEB_URL).
 * Ishga tushirish va kerakli env: tests/e2e/README.md. Testlar bitta bazani bo'lishadi: ketma-ket.
 */
export default defineConfig({
  testDir: "tests/e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_WEB_URL ?? "http://localhost:3000",
    trace: "off",
    screenshot: "only-on-failure",
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH } : {},
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});

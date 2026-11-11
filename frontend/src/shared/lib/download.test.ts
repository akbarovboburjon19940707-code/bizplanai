import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

type FakeWindow = {
  Telegram?: { WebApp?: Record<string, unknown> };
  TelegramWebviewProxy?: unknown;
  location: { href: string; hash: string };
  sessionStorage: Storage;
};

function memoryStorage(): Storage {
  const m = new Map<string, string>();
  return {
    getItem: (k) => m.get(k) ?? null, setItem: (k, v) => void m.set(k, v), removeItem: (k) => void m.delete(k),
    clear: () => m.clear(), key: () => null, get length() { return m.size; },
  };
}

let win: FakeWindow;
let appended: { src: string; onload?: () => void }[];

beforeEach(() => {
  vi.resetModules();
  win = { location: { href: "https://yangi.bizplanai.uz/reja/", hash: "" }, sessionStorage: memoryStorage() };
  appended = [];
  vi.stubGlobal("window", win);
  vi.stubGlobal("document", { createElement: () => ({}), head: { appendChild: (el: { src: string }) => appended.push(el) } });
});
afterEach(() => vi.unstubAllGlobals());

const URL_ = "https://r2.example/plans/a.docx?sig=1";

describe("openDownload", () => {
  it("outside Telegram navigates to the signed URL", async () => {
    const { openDownload } = await import("./download");
    await openDownload(URL_, "Non sexi - biznes reja.docx");
    expect(win.location.href).toBe(URL_);
    expect(appended).toHaveLength(0);
  });

  it("Telegram 8.0+ uses WebApp.downloadFile with a safe file name", async () => {
    const downloadFile = vi.fn();
    win.Telegram = { WebApp: { initData: "x", downloadFile, isVersionAtLeast: (v: string) => v <= "8.0", openLink: vi.fn() } };
    const { openDownload } = await import("./download");
    await openDownload(URL_, "Qo'y «sotib» olish: reja?.pdf");
    expect(downloadFile).toHaveBeenCalledWith({ url: URL_, file_name: "Qoy sotib olish reja.pdf" });
    expect(win.location.href).not.toBe(URL_);
  });

  it("older Telegram opens the link in the external browser", async () => {
    const openLink = vi.fn();
    win.Telegram = { WebApp: { initData: "x", downloadFile: vi.fn(), isVersionAtLeast: () => false, openLink } };
    const { openDownload } = await import("./download");
    await openDownload(URL_, "a.docx");
    expect(openLink).toHaveBeenCalledWith(URL_);
  });

  it("inside Telegram without the SDK on this page, loads the SDK first", async () => {
    win.TelegramWebviewProxy = {};
    const openLink = vi.fn();
    const { openDownload } = await import("./download");
    const done = openDownload(URL_, "a.docx");
    expect(appended[0].src).toBe("https://telegram.org/js/telegram-web-app.js");
    win.Telegram = { WebApp: { initData: "", openLink } };
    appended[0].onload?.();
    await done;
    expect(openLink).toHaveBeenCalledWith(URL_);
  });

  it("remembers the Telegram context across pages via sessionStorage", async () => {
    win.location.hash = "#tgWebAppData=abc";
    const mod = await import("./download");
    mod.markTelegramContext();
    win.location.hash = "";
    expect(win.sessionStorage.getItem("bp_in_telegram")).toBe("1");
  });
});

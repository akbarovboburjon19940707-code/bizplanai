// Telegram Mini App SDK'ning biz ishlatadigan qismi (https://telegram.org/js/telegram-web-app.js)
export type TelegramWebApp = {
  initData: string;
  colorScheme: "light" | "dark";
  ready: () => void;
  expand: () => void;
  HapticFeedback?: { impactOccurred: (style: "light" | "medium" | "heavy") => void };
  version?: string;
  isVersionAtLeast?: (version: string) => boolean;
  /** Bot API 8.0+: fayl Telegram orqali yuklanadi (foydalanuvchi tasdiqlaydi). */
  downloadFile?: (params: { url: string; file_name: string }, callback?: (accepted: boolean) => void) => void;
  /** Havolani tashqi brauzerda ochadi. */
  openLink?: (url: string) => void;
};

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
    /** Telegram mobil/desktop ilovalari WebView'ga qo'shadi (Mini App ichida ekanini bildiradi). */
    TelegramWebviewProxy?: unknown;
  }
}

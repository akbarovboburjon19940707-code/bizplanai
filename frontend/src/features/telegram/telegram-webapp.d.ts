// Telegram Mini App SDK'ning biz ishlatadigan qismi (https://telegram.org/js/telegram-web-app.js)
export type TelegramWebApp = {
  initData: string;
  colorScheme: "light" | "dark";
  ready: () => void;
  expand: () => void;
  HapticFeedback?: { impactOccurred: (style: "light" | "medium" | "heavy") => void };
};

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

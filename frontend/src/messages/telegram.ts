// Telegram Mini App (/tg) matnlari
export const telegramMessages = {
  title: "BizplanAI",
  loading: "Telegram orqali kirilmoqda…",
  outsideTitle: "Bu sahifa Telegram ichida ochiladi",
  outsideText: "Botdagi «📋 Biznes reja yaratish» tugmasini bosing yoki saytga oddiy usulda kiring.",
  toSite: "Saytga kirish",
  errorTitle: "Kirib bo‘lmadi",
  errorText: "Mini App’ni yopib, botdan qayta oching.",
  hello: (name: string) => (name ? `Salom, ${name}!` : "Salom!"),
  subtitle: "Bank talablariga mos biznes-reja bir necha daqiqada",
  actions: {
    create: "Reja yaratish",
    createHint: "Word va Excel, 10 yillik hisob",
    catalog: "Tayyor rejalar",
    tariffs: "Tariflar",
    account: "Kabinet",
  },
} as const;

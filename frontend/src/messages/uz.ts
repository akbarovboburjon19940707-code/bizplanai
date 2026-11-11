import { adminMessages } from "./admin";
import { accountMessages, authMessages } from "./auth";
import { catalogMessages, paymentMessages, tariffMessages } from "./commerce";
import { planMessages } from "./plan";
import { telegramMessages } from "./telegram";

export const uz = {
  appName: "BizplanAI",
  tagline: "Biznes rejangizni ishonch bilan tuzing",
  navigation: {
    home: "Bosh sahifa",
    workspace: "Ish maydoni",
    signIn: "Kirish",
    signUp: "Ro‘yxatdan o‘tish",
    signOut: "Chiqish",
    account: "Kabinet",
    createPlan: "Reja yaratish",
    catalog: "Katalog",
    tariffs: "Tariflar",
    admin: "Admin panel",
    menu: "Menyu",
  },
  auth: {
    loading: "Sessiya tekshirilmoqda",
    guest: "Mehmon",
    signedIn: "Tizimga kirilgan",
  },
  home: {
    eyebrow: "Bank talablariga mos biznes-reja",
    title: "G‘oyadan bankka topshiriladigan biznes-rejagacha",
    description:
      "Loyihangiz ma’lumotlarini kiriting: kredit muddatiga mos (10 yilgacha) moliyaviy model, NPV, IRR va qoplash muddati hisoblanadi, Word va Excel hujjatlar tayyor bo‘ladi.",
    primaryAction: "Reja yaratish",
    secondaryAction: "Tayyor rejalar",
    phaseLabel: "Ro‘yxatdan o‘tmasdan ham ko‘rsatkichlarni hisoblab ko‘ring",
    stepsTitle: "3 bosqichda tayyor",
    steps: [
      { title: "Ma’lumot kiriting", text: "Faoliyat turi, loyiha qiymati, kredit, mahsulot va xodimlar. Ko‘rsatkichlar yozish davomida hisoblanadi." },
      { title: "Natijani tekshiring", text: "NPV, IRR, qoplash muddati va yillik jadvallar bir sahifada." },
      { title: "Hujjatni yuklab oling", text: "Bank shabloniga mos Word hujjat va formulali Excel jadvallar." },
    ],
    featuresTitle: "Nega BizplanAI",
    features: [
      { title: "Bank shabloni", text: "Hisob-kitob bank amaliyotidagi NPV shabloni asosida, davr kredit muddatiga moslanadi." },
      { title: "Jonli hisob", text: "Har o‘zgarishda ko‘rsatkichlar darhol qayta hisoblanadi." },
      { title: "AI matn", text: "Tarifga qarab loyiha tavsifi va bozor tahlili AI yordamida yoziladi." },
      { title: "Telegram", text: "Bot va Mini App orqali telefondan ham ishlaydi." },
    ],
    popularTitle: "Mashhur tayyor rejalar",
    allCatalog: "Barcha rejalar →",
    tariffsTitle: "Tariflar",
    allTariffs: "Batafsil →",
    ctaTitle: "Birinchi rejangizni bugun yarating",
    ctaText: "Bepul tarifda kuniga 3 ta reja.",
  },

  footer: "Biznes rejalash uchun yagona ish maydoni.",
  plans: planMessages,
  authForms: authMessages,
  account: accountMessages,
  catalog: catalogMessages,
  tariffs: tariffMessages,
  payments: paymentMessages,
  admin: adminMessages,
  telegram: telegramMessages,
} as const;

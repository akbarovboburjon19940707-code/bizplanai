import { adminMessages } from "./admin";
import { accountMessages, authMessages } from "./auth";
import { catalogMessages, paymentMessages, tariffMessages } from "./commerce";
import { planMessages } from "./plan";

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
    eyebrow: "Biznes rejalash platformasi",
    title: "G‘oyadan puxta biznes rejagacha",
    description:
      "Loyihangizni tartib bilan rejalashtiring, moliyaviy ko‘rsatkichlarni ko‘ring va keyingi qadamlarni belgilang.",
    primaryAction: "Ish maydoniga o‘tish",
    phaseLabel: "Ro‘yxatdan o‘tmasdan ham ko‘rsatkichlarni hisoblab ko‘ring",
  },
  footer: "Biznes rejalash uchun yagona ish maydoni.",
  plans: planMessages,
  authForms: authMessages,
  account: accountMessages,
  catalog: catalogMessages,
  tariffs: tariffMessages,
  payments: paymentMessages,
  admin: adminMessages,
} as const;

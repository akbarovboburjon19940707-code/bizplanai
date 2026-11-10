import { accountMessages, authMessages } from "./auth";
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
} as const;

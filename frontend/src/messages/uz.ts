import { planMessages } from "./plan";

export const uz = {
  appName: "BizplanAI",
  tagline: "Biznes rejangizni ishonch bilan tuzing",
  navigation: {
    home: "Bosh sahifa",
    workspace: "Ish maydoni",
    signIn: "Kirish",
    signOut: "Chiqish",
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
    phaseLabel: "Yangi platforma bosqichi 1",
  },
  footer: "Biznes rejalash uchun yagona ish maydoni.",
  plans: planMessages,
} as const;

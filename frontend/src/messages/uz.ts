import { adminMessages } from "./admin";
import { assistantMessages } from "./assistant";
import { accountMessages, authMessages } from "./auth";
import { catalogMessages, paymentMessages, tariffMessages } from "./commerce";
import { contactMessages } from "./contact";
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
    contact: "Aloqa",
    faq: "Savollar",
    menu: "Menyu",
  },
  auth: {
    loading: "Sessiya tekshirilmoqda",
    guest: "Mehmon",
    signedIn: "Tizimga kirilgan",
  },
  home: {
    eyebrow: "Bank talablariga mos biznes-reja",
    titleStart: "Kredit uchun biznes-reja ",
    titleAccent: "3 daqiqada",
    titleEnd: ", bank formatida",
    description:
      "Ma’lumotlarni kiriting: NPV, IRR, qoplash muddati va kredit muddatiga mos moliyaviy model avtomatik hisoblanadi. Natija: Word hujjat va Excel jadvallar.",
    primaryAction: "Bepul hisoblashni boshlash",
    secondaryAction: (n: number) => (n > 0 ? `${n} ta tayyor reja` : "Tayyor rejalar"),
    highlights: ["Hisob-kitob ro‘yxatdan o‘tmasdan", "1–10 yillik moliyaviy model", "Click va Payme orqali to‘lov", "Telegram bot va Mini App"],
    preview: {
      sample: "Namuna",
      excelName: "moliyaviy_model.xlsx",
      wordName: "biznes_reja.docx",
      docKind: "Biznes-reja",
      docTitle: "Non va qandolat sexi",
      unit: "mln so‘m",
      year: (n: number) => `${n}-yil`,
      rows: [
        { label: "Tushum", values: ["980", "1 150", "1 240"] },
        { label: "Xarajatlar", values: ["702", "790", "836"] },
        { label: "Kredit to‘lovi", values: ["118", "112", "106"] },
        { label: "Sof pul oqimi", values: ["160", "248", "298"], total: true },
      ],
      metrics: [["NPV", "186 mln"], ["IRR", "34%"], ["Qoplash", "2,3 yil"]],
      ready: "Hujjat tayyor",
      readyText: "Word + Excel",
    },
    stats: (plans: number) => [
      { value: plans > 0 ? String(plans) : "200+", label: "tayyor biznes-reja katalogda" },
      { value: "10 yil", label: "gacha moliyaviy prognoz" },
      { value: "Word + Excel", label: "bank shablonidagi hujjat va jadvallar" },
      { value: "24/7", label: "sayt va Telegram bot" },
    ],
    contentsEyebrow: "Hujjat tarkibi",
    contentsTitle: "Bank kredit bo‘limi so‘raydigan hamma narsa",
    contentsText: "Bo‘limlar bank shabloni tartibida. Saytda bitta qiymatni o‘zgartirsangiz, barcha jadval va ko‘rsatkichlar darhol qayta hisoblanadi.",
    contents: [
      { icon: "📄", title: "Loyiha tavsifi", text: "Korxona, mahsulot, bozor, marketing va xodimlar rejasi." },
      { icon: "🏦", title: "Kredit jadvali", text: "Asosiy qarz va foiz to‘lovlari, imtiyozli davr bilan." },
      { icon: "📈", title: "Pul oqimi va foyda", text: "Yillar bo‘yicha tushum, xarajat, soliq, amortizatsiya va sof foyda." },
      { icon: "🎯", title: "NPV, IRR, qoplash", text: "Bank baholaydigan samaradorlik ko‘rsatkichlari va zararsizlik nuqtasi." },
      { icon: "🧾", title: "Investitsiya smetasi", text: "Uskunalar, qurilish va aylanma mablag‘, moliyalash manbalari bilan." },
      { icon: "✍️", title: "Bo‘limlar matni", text: "Loyiha tavsifi, bozor tahlili va xulosalar tayyor matn bilan." },
    ],
    stepsTitle: "3 qadam, hisob-kitob ro‘yxatdan o‘tmasdan",
    steps: [
      { title: "Ma’lumot kiriting", text: "Faoliyat turi, loyiha qiymati, kredit summasi va muddati, mahsulotlar." },
      { title: "Bepul natijani ko‘ring", text: "NPV, IRR, qoplash muddati va yillik jadvallar ekranda darhol." },
      { title: "Hujjatni yuklab oling", text: "To‘lovdan keyin Word hujjat va Excel jadvallar shu zahoti tayyor." },
    ],
    popularEyebrow: "Tayyor rejalar",
    popularTitle: "Sohangiz bo‘yicha tayyor biznes-reja",
    allCatalog: (n: number) => (n > 0 ? `Barcha ${n} ta reja →` : "Barcha rejalar →"),
    allCategories: "Hammasi",
    tariffsTitle: "Narxlar",
    tariffsText: "Hisob-kitob har doim bepul. Hujjat uchun to‘laysiz.",
    popularBadge: "Eng ommabop",
    singleFeatures: ["1 ta reja: Word + Excel", "Barcha jadvallar va ko‘rsatkichlar", "Muddati cheklanmagan"],
    wordExcel: "Word + Excel",
    choose: "Tanlash",
    payWith: "To‘lov:",
    faqTitle: "Ko‘p beriladigan savollar",
    faq: [
      {
        q: "Bank bu hujjatni qabul qiladimi?",
        a: "Ha. Hujjat tijorat banklari kredit bo‘limlari talab qiladigan shablon asosida tuziladi: bo‘limlar, jadvallar va NPV/IRR ko‘rsatkichlari bank formatida. Kredit bo‘yicha yakuniy qarorni bank qabul qiladi.",
      },
      {
        q: "Ro‘yxatdan o‘tish shartmi?",
        a: "Hisob-kitobni (NPV, IRR, jadvallar) ro‘yxatdan o‘tmasdan bepul ko‘rishingiz mumkin. Rejani saqlash va Word/Excel hujjatni olish uchun ro‘yxatdan o‘tish shart: telefon raqami yoki Telegram orqali, 1 daqiqada.",
      },
      {
        q: "To‘lovdan keyin hujjat qachon tayyor bo‘ladi?",
        a: "Shu zahoti: Click yoki Payme orqali to‘lov tasdiqlangach, hujjat bir necha soniyada tayyorlanadi va kabinetingizda yuklab olinadi.",
      },
      {
        q: "Excel faylda nima bo‘ladi?",
        a: "Excel faylda barcha jadvallar tayyor hisoblangan raqamlar bilan beriladi (formulalar ichida emas). Ma’lumotni o‘zgartirmoqchi bo‘lsangiz, saytda kiritasiz: barcha ko‘rsatkichlar darhol qayta hisoblanadi.",
      },
      {
        q: "Tayyor reja bilan o‘zim yaratgan reja o‘rtasida qanday farq bor?",
        a: "Tayyor reja: katalogdagi aniq soha bo‘yicha tuzilgan PDF biznes-reja, to‘lovdan keyin darhol yuklab olinadi va namuna sifatida qulay. O‘zingiz yaratgan reja esa aynan sizning raqamlaringiz (loyiha qiymati, kredit, mahsulotlar) asosida hisoblanadi va Word hamda Excel shaklida beriladi.",
      },
      {
        q: "Qanday to‘lash mumkin?",
        a: "Click yoki Payme orqali: to‘lov bir zumda tasdiqlanadi. Kartaga o‘tkazma ham mumkin: chek rasmini yuklaysiz, administrator tekshirib tasdiqlaydi.",
      },
      {
        q: "Kredit muddati hisob-kitobga qanday ta’sir qiladi?",
        a: "Kredit muddatini oyda kiritasiz, masalan 36 oy. Loyiha davri shu muddatga moslanadi: jadvallar, amortizatsiya, NPV va IRR aynan 3 yil uchun hisoblanadi. Muddat 10 yilgacha bo‘lishi mumkin.",
      },
      {
        q: "Hujjatni keyinroq qayta yuklab olsam bo‘ladimi?",
        a: "Ha. Yaratgan rejalaringiz kabinetdagi «Rejalarim» bo‘limida saqlanadi, Word va Excel’ni istalgan vaqtda qayta yuklab olasiz. Sotib olgan tayyor rejani esa uning sahifasidan qayta yuklab olish mumkin.",
      },
      {
        q: "Tarifdagi limitlar nima degani?",
        a: "Har tarifda kuniga va oyiga nechta reja yaratish mumkinligi belgilangan (yuqoridagi «Narxlar» bo‘limida). Obuna 30 kun amal qiladi. Limit tugasa, obunani kutmasdan bitta rejani alohida sotib olishingiz mumkin.",
      },
      {
        q: "Telefondan foydalansa bo‘ladimi?",
        a: "Ha. Sayt telefonga moslashgan, shuningdek Telegram bot va Mini App orqali ham reja yaratib, hujjatni olishingiz mumkin.",
      },
      {
        q: "Ma’lumotlarim xavfsizmi?",
        a: "Sayt bilan aloqa shifrlangan (HTTPS). Hujjatlaringiz yopiq omborda saqlanadi va faqat sizga, qisqa muddatli shaxsiy havola orqali beriladi. Ma’lumotlaringiz faqat xizmat ko‘rsatish uchun ishlatiladi va hech kimga sotilmaydi.",
      },
      {
        q: "Savolim bo‘lsa, kimga murojaat qilaman?",
        a: "Saytdagi «Savol berish» tugmasi orqali darhol yozing yoki Telegram va telefon orqali bog‘laning: dushanbadan shanbagacha, 9:00–19:00. Barcha aloqa ma’lumotlari sahifa pastida.",
      },
    ],
    ctaTitle: "Rejangiz raqamlarini hozir bepul ko‘ring",
    ctaText: "Hisob-kitob uchun ro‘yxatdan o‘tish shart emas. Natija darhol ekranda.",
    ctaAction: "Hisoblashni boshlash →",
  },

  footer: "Biznes rejalash uchun yagona ish maydoni.",
  plans: planMessages,
  authForms: authMessages,
  contact: contactMessages,
  assistant: assistantMessages,
  account: accountMessages,
  catalog: catalogMessages,
  tariffs: tariffMessages,
  payments: paymentMessages,
  admin: adminMessages,
  telegram: telegramMessages,
} as const;

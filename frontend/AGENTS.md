# BizplanAI frontend: Codex uchun topshiriq

Sen shu loyihaning **frontend** qismini noldan yozasan. Backend tayyor va alohida (Claude yozgan, FastAPI).
Sen backendga **tegmaysan**; u bilan faqat `docs/API_CONTRACT.md` va `docs/openapi.json` orqali gaplashasan.

## 0. Ishni boshlashdan oldin o'qi

1. `docs/API_CONTRACT.md`: har endpoint, xato kodlari, token qoidasi, majburiy sahifalar. **Asosiy manba.**
2. `docs/openapi.json`: aniq sxemalar. Tiplarni undan generatsiya qil:
   `npx openapi-typescript docs/openapi.json -o src/shared/api/schema.d.ts`
3. `reference/old-site/`: eski saytning HTML/CSS/JS fayllari. **Faqat UI/UX, matnlar va forma maydonlari uchun namuna.**
   Koddan nusxa ko'chirma: u yerda `innerHTML` orqali XSS, `localStorage` da token va boshqa xavfsizlik muammolari bor.

Kontraktda yetishmaydigan narsa kerak bo'lsa, endpoint **o'ylab topma** va backendni o'zgartirma:
`docs/CONTRACT_REQUESTS.md` ga yoz (nima kerak, qaysi sahifa uchun, taklif qilingan javob shakli) va shu qismni vaqtincha o'chirib/yashirib qo'y.

## 1. Texnologiyalar (o'zgartirma)

| Qatlam | Tanlov |
| --- | --- |
| Framework | Next.js 15 (App Router), React 19, TypeScript `strict` |
| Chiqish | **Static export**: `output: "export"`, `trailingSlash: true`. Server komponentlar ishlamaydi, Render Static Site (CDN) ga joylanadi |
| Stil | Tailwind CSS, komponentlar uchun shadcn/ui (Radix) |
| Server holati | TanStack Query v5 |
| Formalar | React Hook Form + Zod |
| API klient | `openapi-typescript` tiplari + `openapi-fetch` (yoki 100 qatorlik o'z `fetch` wrapperi) |
| Til | Faqat o'zbek (lotin). Barcha matnlar `src/messages/uz.ts` da, komponentlarga qattiq yozilmaydi (keyin rus tili qo'shiladi) |
| Test | Vitest + Testing Library (birlik), Playwright (e2e) |
| Sifat | ESLint (`react/no-danger` va `no-restricted-syntax: innerHTML` xato beradi), Prettier |

Paket menejeri: `npm`. Node 20 LTS.

## 2. Papka tuzilmasi

```
frontend/
  src/
    app/                      # faqat yo'nalishlar (page.tsx, layout.tsx), mantiq features/ da
      (marketing)/page.tsx            # /
      kirish/  royxat/
      dashboard/page.tsx              # reja yaratish ustasi
      reja/page.tsx                   # ?id=...  (reja holati va yuklash)
      kabinet/page.tsx
      katalog/page.tsx  katalog/[slug]/page.tsx
      tariflar/page.tsx
      tolov/[id]/page.tsx             # Click/Payme dan qaytish
      tg/page.tsx                     # Telegram Mini App
      admin/ (layout, page, tolovlar, foydalanuvchilar, katalog)
      not-found.tsx
    features/ { auth, plans, catalog, payments, billing, admin, telegram }/   # hook + komponent + zod sxema
    shared/
      api/        # client.ts, schema.d.ts (generatsiya), errors.ts
      ui/         # shadcn komponentlar
      lib/        # format.ts (so'm, sana), cn.ts
    messages/uz.ts
  public/
  tests/e2e/
  next.config.ts  tailwind.config.ts  .env.example
```

## 3. Dizayn

Eski sayt vizual yo'nalishini saqla (foydalanuvchilar unga o'rgangan), lekin tartibli va zamonaviy qil. Tokenlar:

| Token | Qiymat |
| --- | --- |
| Asosiy ko'k | `#2563eb` (hover `#1d4ed8`, to'q `#1e3a8a`) |
| Hero gradient | `linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #1d4ed8 100%)` |
| Matn / ikkilamchi / xira | `#0f172a` / `#64748b` / `#94a3b8` |
| Fon / sirt / chegara | `#f0f2f5` / `#ffffff` / `#e2e8f0` |
| Muvaffaqiyat / ogohlantirish / xavf / aksent | `#22c55e` / `#f59e0b` / `#ef4444` / `#8b5cf6` |
| Radius | 16px (kartalar), 10px (input, tugma) |
| Shriftlar | Sarlavhalar **Outfit**, matn **Inter** (`next/font`, lotin + `latin-ext`) |

Mobil birinchi: foydalanuvchilarning katta qismi telefon va Telegram ichida. 360px dan 1440px gacha tekshir.
Dark mode shart emas (Telegram Mini App `/tg` sahifasi Telegram mavzusiga `--tg-*` o'zgaruvchilari orqali moslashadi).

## 4. Sahifalar va talablar

Har sahifada: yuklanish (skeleton), bo'sh holat, xato holati (kontraktdagi `error.message`), mobil ko'rinish.

| Yo'l | Mazmuni | Muhim |
| --- | --- | --- |
| `/` | Landing: hero, "3 bosqichda reja yarating", imkoniyatlar, tariflar (`GET /v1/tariffs`), katalogdan 6 ta mashhur reja, CTA | SEO: title, description, OpenGraph |
| `/kirish`, `/royxat` | Telefon + parol; Telegram orqali kirish (bot oqimi, kontrakt 2-bo'lim); `totp_required` kelsa 6 xonali kod maydoni | Telefon niqobi `+998 XX XXX XX XX`; xatolar maydon ostida |
| `/dashboard` | Reja yaratish ustasi (5 bosqich, 5-bo'lim) | Kirmagan foydalanuvchi to'ldira oladi, "Yaratish" bosilganda kirishga yo'naltiriladi va kiritilgan ma'lumot yo'qolmaydi (`sessionStorage`da faqat forma ma'lumoti, token emas) |
| `/reja?id=` | Holat (`queued/running/done/failed`) har 2 s polling, tayyor bo'lsa Word va Excel yuklash | `failed` da "kvota qaytarildi" xabari |
| `/kabinet` | Profil, joriy tarif va limit chizig'i (`daily_used/daily_limit`), rejalarim, to'lovlarim, parol almashtirish | |
| `/katalog` | 6 kategoriya, qidiruv (debounce), sahifalash (`limit/offset`) | URL query bilan (`?category=&q=&page=`) |
| `/katalog/[slug]` | Mahsulot, narx, "Sotib olish"; sotib olgan bo'lsa "Yuklab olish" | `generateStaticParams`: build vaqtida API'dan hammasini oladi (6-bo'lim) |
| `/tariflar` | Tariflar jadvali, "Tanlash" -> to'lov usuli oynasi | `quota_exceeded` shu yerga keladi |
| `/tolov/[id]` | Click/Payme'dan qaytgach holatni 3 s polling bilan kuzatadi: `paid` -> muvaffaqiyat; `pending` 2 daqiqadan oshsa "hali tasdiqlanmadi" | Manual to'lovda chek yuklash formasi shu yerda ham |
| `/tg` | Telegram Mini App: `initData` bilan avtomatik kirish, ixcham dashboard | `https://telegram.org/js/telegram-web-app.js` faqat shu sahifada yuklanadi |
| `/admin/*` | Statistika, to'lovlar navbati (chekni ko'rish, tasdiqlash/rad), foydalanuvchilar, katalog tahriri | `role !== "admin"` bo'lsa 404 ko'rsat. Admin ham `/kirish` orqali (TOTP bilan) kiradi |

### To'lov oynasi (umumiy komponent)
`GET /v1/payments/methods` dan faqat `true` usullar ko'rsatiladi. `POST /v1/payments`; `checkout.type`:
`redirect` -> `window.location.href = url`; `manual` -> karta raqami (nusxalash tugmasi), summa, ko'rsatma, chek yuklash.
Summani **hech qachon** frontend yubormaydi.

## 5. Reja yaratish ustasi (`/dashboard`)

Maydon nomlari `PlanInput` bilan **aynan bir xil** (`docs/openapi.json`). Zod sxemasi backend chegaralariga mos:
`stir` 9 raqam, `foiz` 0-100, `muddat` 1-360 oy, musbat summalar, va h.k.

1. **Loyiha**: `faoliyat_turi` (4 ta karta), `loyiha_nomi`, `mahsulot`, `olchov`, `manzil`, `tashabbuskor`, `fio`, `mulk`, `stir`, `soliq_turi`, `bank`
2. **Moliya**: `loyiha_qiymati`, `oz_mablag`, `kredit`, `foiz`, `muddat`, `imtiyoz`, `kredit_turi`
3. **Ishlab chiqarish / savdo**: `hajm`, `narx` va sohaga mos xarajatlar: ishlab chiqarish (`xomashyo_narx`, `elektr`, `gaz`, `suv`, `oqava`), qishloq xo'jaligi (`urug_yem_narx`, `texnika_xarajat`, `yer_ijarasi`), savdo (`tovar_xaridi`, `dokon_ijarasi`), xizmat (`joy_ijarasi`, `transport_xarajat`)
4. **Xodimlar**: `direktor`, `rahbar_oylik`, `xodim`, `ishchi_oylik`, `yangi_xodim`, `yangi_ishchi_oylik`
5. **Natija**: `POST /v1/plans/preview` dan NPV, IRR, qoplash muddati, PI, ROI (kartalar) + yillik jadvallar; "AI bilan to'ldirish" belgisi (`use_ai`); "Yaratish"

Qoidalar: `loyiha_qiymati = oz_mablag + kredit` tekshiruvini yumshoq ogohlantirish sifatida ko'rsat (xato emas).
Preview 500 ms debounce, oldingi so'rovni bekor qil (`AbortController`). Summa maydonlarida minglik ajratgich (`1 000 000`), serverga raqam yuboriladi.
Qaysi maydon qaysi bosqichda va qanday yorliq bilan ekanini `reference/old-site/templates/dashboard.html` dan ol.
`403/429 quota_exceeded` -> `/tariflar` ga taklif oynasi.

## 6. Static export bilan ishlash qoidalari

Next static export'da yo'nalish build vaqtida ma'lum bo'lishi kerak:

- `/tolov/[id]`: `generateStaticParams` -> `[{ id: "_" }]`, `dynamicParams = false`. Haqiqiy `id` ni `window.location.pathname` dan o'qi
  (sahifa client komponent). Render rewrite: `/tolov/*` -> `/tolov/_/index.html`.
- `/katalog/[slug]`: build vaqtida `GET /v1/catalog/products?limit=100&offset=...` bilan hamma sahifani aylanib chiq. Yangi mahsulot qo'shilganda
  qayta deploy kerak (Render Deploy Hook). Build vaqtida API javob bermasa, build **xato bilan to'xtasin** (bo'sh katalog bilan chiqmasin).
- `/reja?id=` va admin ichki sahifalar query yoki client routing bilan; dinamik segment ishlatma.
- `next/image` o'rniga oddiy `<img loading="lazy" width height>` (static export'da optimizer yo'q); katalog rasmlari Cloudflare R2 URL'laridan keladi.

Render bloki allaqachon qo'shilgan: repo ildizidagi `render.staging.yaml` va `render.production.yaml` (`bizplan-*-web`). Quyidagi asl taklif ma'lumot uchun:

```yaml
- type: web
  name: bizplan-frontend
  runtime: static
  rootDir: frontend
  buildCommand: npm ci && npm run build
  staticPublishPath: out
  envVars:
    - { key: NEXT_PUBLIC_API_URL, value: https://api.bizplanai.uz }
  routes:
    - { type: rewrite, source: /tolov/*, destination: /tolov/_/index.html }
  headers:
    - { path: /*, name: X-Content-Type-Options, value: nosniff }
    - { path: /*, name: Referrer-Policy, value: strict-origin-when-cross-origin }
    - { path: /*, name: Content-Security-Policy, value: "default-src 'self'; script-src 'self' 'unsafe-inline' https://telegram.org; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.bizplanai.uz; frame-ancestors 'self' https://*.telegram.org" }   # Telegram Web Mini App'ni iframe'da ochadi
```

CSP'ni haqiqiy ishlaydigan holga keltirish (Next inline skriptlari uchun nonce/hash kerak bo'lsa) sening vazifang.

## 7. API klient va autentifikatsiya (kritik)

- `access_token` **faqat xotirada** (modul o'zgaruvchisi yoki React context). `localStorage`, `sessionStorage`, cookie'ga **yozilmaydi**.
- Barcha so'rovlar `credentials: "include"`. Base URL: `process.env.NEXT_PUBLIC_API_URL` (build vaqtida). Foydalanuvchi tomonidan o'zgartirib bo'lmaydi.
- Ilova ochilganda `POST /v1/auth/refresh`: 200 -> kirgan, 401 -> mehmon. Bu bosqichda sahifa miltillamasin (skeleton).
- 401 kelsa: **bitta** umumiy refresh promise, keyin asl so'rovni 1 marta qaytar. `token_reused` -> darhol chiqish.
- Xatolarni `{error:{code,message,details}}` bo'yicha `ApiError` sinfiga o'gir. Mantiq `code` bo'yicha, ko'rsatish `message`.
- `422 validation_error`: `details[].field` ni React Hook Form maydonlariga `setError` qil.
- `429 rate_limited`: tugmani 5 soniya blokla.
- Yuklash: `GET .../download` -> `{url}` -> `window.location.href = url`. URL'ni o'zing yasama.

## 8. Xavfsizlik (buzilsa PR qabul qilinmaydi)

- `dangerouslySetInnerHTML`, `innerHTML`, `eval`, `document.write` yo'q. Foydalanuvchi matni (reja nomi va h.k.) faqat JSX orqali chiqadi.
- Tashqi skript faqat `/tg` sahifasida Telegram'niki.
- Chek yuklashda fayl turi (`jpg/png/webp/pdf`) va hajm (10 MB) mijoz tomonida ham tekshiriladi (server baribir tekshiradi).
- Konsolga token, telefon, to'lov ma'lumoti chiqarma. Analitika qo'shma.
- Karta raqami, Click/Payme kalitlari va boshqa maxfiy narsalar frontend kodida bo'lmaydi: hammasi API'dan keladi.

## 9. Sifat mezonlari

| Mezon | Chegara |
| --- | --- |
| Lighthouse (mobil, `/` va `/katalog`) | Performance >= 90, Accessibility >= 95, SEO >= 95 |
| Birinchi yuklanish JS | `/` uchun <= 150 KB gzip (landing'da og'ir kutubxona yo'q) |
| Klaviatura va ekran o'qigich | Barcha tugma/formalar fokus ko'rinadi, `label` bor, oyna `Esc` bilan yopiladi |
| TypeScript | `strict`, `any` yo'q (zarurat bo'lsa izoh bilan) |
| Komponent hajmi | Fayl 250 qatordan oshmasin; mantiq hook'ga chiqariladi |

Buyruqlar (hammasi `package.json` da va CI'da yashil bo'lishi shart):
`npm run lint`, `npm run typecheck`, `npm test`, `npm run build`, `npm run e2e`, `npm run gen:api` (openapi tiplarini yangilash).

## 10. Backendni lokal ishga tushirish (integratsiya uchun)

Backend ZIP'i alohida (`bizplanai_backend.zip`). Tashqarida:

```bash
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt && cp .env.example .env
alembic upgrade head && python -m app.cli seed
uvicorn app.main:app --port 8000          # Swagger: http://localhost:8000/docs
```

`.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`. Dev'da Redis kerak emas, reja so'rov ichida yaratiladi.
To'lov usullari `/v1/payments/methods` da `false` bo'lishi normal (kalitlar yo'q): bu holatni ham UI'da to'g'ri ko'rsat.
Qo'lda to'lovni sinash uchun backend `.env` ga `MANUAL_CARD_NUMBER=8600 0000 0000 0000` qo'y.

## 11. Ish tartibi (shu ketma-ketlikda, har bosqich alohida commit/PR)

| # | Bosqich | Tayyor bo'lish mezoni |
| --- | --- | --- |
| 1 | Loyiha skeleti: Next, Tailwind, shadcn, ESLint qoidalari, API klient, `ApiError`, auth context (refresh oqimi), layout, header/footer | `lint`, `typecheck`, `build` yashil; kirgan/mehmon holati almashadi |
| 2 | `/kirish`, `/royxat`, Telegram bot orqali kirish, `/kabinet` (profil, limit) | Ro'yxatdan o'tib, sahifa yangilanganda sessiya saqlanadi (refresh cookie) |
| 3 | `/dashboard` ustasi + jonli preview + `/reja` holat va yuklash | Haqiqiy backend bilan Word va Excel yuklab olinadi; `quota_exceeded` ko'rsatiladi |
| 4 | `/katalog`, `/katalog/[slug]`, `/tariflar`, to'lov oynasi, `/tolov/[id]`, chek yuklash | Qo'lda to'lov: chek yuklanadi, admin tasdiqlagach "paid" bo'ladi |
| 5 | `/` landing, SEO (sitemap, robots, OG), 404, `/tg` Mini App | Lighthouse mezonlari bajarilgan |
| 6 | `/admin/*` | Admin TOTP bilan kiradi, to'lovni tasdiqlaydi, katalog narxini o'zgartiradi |
| 7 | e2e (Playwright): ro'yxat -> reja yaratish -> yuklash; to'lov oqimi; admin tasdiqlash. `render.yaml` bloki va README | Hammasi CI'da yashil |

Har bosqich oxirida qisqa hisobot yoz: nima qilindi, nima sinaldi, `CONTRACT_REQUESTS.md` da nima qoldi.

## 12. Qilma

- Backend kodini, API yo'llarini yoki javob shakllarini o'zgartirma.
- Mock ma'lumot bilan "ishlayapti" deb qoldirma: har sahifa haqiqiy backend bilan sinalgan bo'lsin.
- Eski saytdan "AI rasm yaratish", "STIR bo'yicha avtoto'ldirish" kabi funksiyalarni ko'chirma: ular soxta edi va backendda yo'q.
- Narx, limit, tarif nomlarini kodda qattiq yozma: `GET /v1/tariffs` va `/v1/catalog` dan ol.

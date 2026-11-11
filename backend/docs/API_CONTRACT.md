# BizplanAI API kontrakti (v1)

Frontend (Codex) va backend (Claude) shu hujjat va `docs/openapi.json` bo'yicha integratsiya qilinadi.
Kontrakt o'zgarsa, avval shu fayl va `openapi.json` yangilanadi, keyin kod.

TypeScript tiplari: `npx openapi-typescript docs/openapi.json -o src/shared/api/schema.d.ts`

## 1. Asosiy qoidalar

| Narsa | Qiymat |
| --- | --- |
| Production API | `https://api.bizplanai.uz` |
| Lokal API | `http://localhost:8000` (Swagger: `/docs`, faqat dev) |
| CORS ruxsat etilgan frontend | `https://bizplanai.uz`, `https://www.bizplanai.uz`, lokal `http://localhost:3000` |
| Versiya | Hamma yo'l `/v1/...` bilan boshlanadi |
| Format | JSON, UTF-8. Chek yuklash: `multipart/form-data`, maydon nomi `file` |
| Pul | Javoblarda butun so'm (`price_som`, `amount_som`). Tiyin frontendga chiqmaydi |
| Vaqt | ISO 8601, UTC |

### Xato formati (hamma xatolar bir xil)

```json
{ "error": { "code": "quota_exceeded", "message": "Limit tugadi...", "details": { "upgrade_url": "/tariflar" } } }
```

Frontend `message` ni foydalanuvchiga ko'rsatadi, mantiqni `code` bo'yicha quradi.

| HTTP | code | Frontend nima qiladi |
| --- | --- | --- |
| 401 | `unauthorized` | Bir marta `/v1/auth/refresh`, so'rovni qaytaradi; yana 401 bo'lsa kirish sahifasi |
| 401 | `token_reused` | Darhol chiqish, "xavfsizlik sababli qayta kiring" |
| 401 | `invalid_credentials`, `totp_required`, `totp_invalid` | Kirish formasida xabar; `totp_required` bo'lsa 6 xonali kod maydonini ochadi |
| 403 | `forbidden`, `not_purchased` | Ruxsat yo'q / sotib olish tugmasi |
| 404 | `not_found`, `file_missing` | Topilmadi xabari |
| 409 | `phone_taken`, `already_owned`, `not_ready`, `bad_state` | Mos xabar |
| 422 | `validation_error` | `details[]` dagi `field` bo'yicha forma maydonlarini belgilaydi |
| 429 | `rate_limited` | "Biroz kuting", tugmani 5-10 soniya bloklaydi |
| 429 | `quota_exceeded` | `details.upgrade_url` (`/tariflar`) ga taklif |

## 2. Autentifikatsiya

- `access_token` 15 daqiqa yashaydi va **faqat xotirada** (React state) saqlanadi. `localStorage` ishlatilmaydi.
- Har so'rovda: `Authorization: Bearer <access_token>`.
- Refresh token httpOnly cookie'da (`bp_refresh`, path `/v1/auth`); JS uni ko'rmaydi. `/v1/auth/*` so'rovlari `credentials: "include"` bilan yuboriladi.
- Sahifa ochilganda `POST /v1/auth/refresh`: 200 bo'lsa foydalanuvchi kirgan, 401 bo'lsa mehmon.
- Bir vaqtda bir nechta 401 kelsa, refresh **bitta** bajariladi (umumiy promise), qolganlari kutadi.
- Bir nechta tab bir vaqtda refresh qilsa (30 soniya ichida bir xil eski cookie), server hammasiga yangi sessiya beradi; `token_reused` faqat 30 soniyadan keyingi qayta ishlatishda qaytadi.

| Metod va yo'l | Body | Javob |
| --- | --- | --- |
| `POST /v1/auth/register` | `{phone, password(8+), first_name?}` | 201 `TokenOut` |
| `POST /v1/auth/login` | `{phone, password, totp_code?}` | `TokenOut` |
| `POST /v1/auth/refresh` | bo'sh | `TokenOut` (cookie yangilanadi) |
| `POST /v1/auth/logout` | bo'sh | 204 |
| `POST /v1/auth/telegram/webapp` | `{init_data: Telegram.WebApp.initData}` | `TokenOut` |
| `POST /v1/auth/telegram/login-init` | bo'sh | `{token, bot_url, expires_in}` |
| `GET /v1/auth/telegram/login-poll?token=` | | `{status: pending/expired/authenticated, session?}` |
| `POST /v1/auth/password-reset/init` | `{phone}` | `{token, bot_url, expires_in: 600}` (raqam bazada bo'lmasa ham 200) |
| `GET /v1/auth/password-reset/poll?token=` | | `{status: pending/verified/mismatch/expired}` |
| `POST /v1/auth/password-reset/complete` | `{token, new_password(8+)}` | `{session: TokenOut \| null}`; 400 `reset_invalid` |

`TokenOut = {access_token, token_type, expires_in, user: {id, phone, email, first_name, last_name, telegram_username, role, plan_credits, has_password}}`

`has_password: false` (Telegram orqali ro'yxatdan o'tgan): parol almashtirishda `current_password` so'ralmaydi.

Telefon istalgan ko'rinishda yuborilishi mumkin (`90 123 45 67`, `+998...`); server `+998XXXXXXXXX` ga keltiradi.

- **Telegram Mini App** (`/tg`): ochilganda `window.Telegram.WebApp.initData` bilan `/telegram/webapp` chaqiriladi.
- **Bot orqali kirish** (oddiy brauzerda): `login-init`, `bot_url` ni yangi oynada ochish, har 2 soniyada `login-poll` (300 soniyagacha).
- **Parolni tiklash** (`/parol-tiklash`, 2026-11-11): telefon > `password-reset/init` > `bot_url` ni ochish; botda "Raqamimni yuborish" (Telegram tasdiqlagan raqam hisobdagi raqam bilan solishtiriladi) > har 2 s `poll` > `verified` bo'lsa yangi parol > `complete`. `session` bo'lsa darhol kiradi; `null` (admin, TOTP) bo'lsa `/kirish`. `mismatch`: raqam mos emas, qaytadan boshlash. Barcha eski sessiyalar yopiladi, kirish bloki olinadi. Parolsiz (Telegram orqali ochilgan) hisoblar tiklanmaydi: ular Telegram orqali kiradi.

## 3. Foydalanuvchi

| Metod va yo'l | Tavsif |
| --- | --- |
| `GET /v1/me` | `{user, subscription: {tariff_code, tariff_name, status: free/active, ends_at, daily_limit, monthly_limit, daily_used, monthly_used, ai_enabled}}` |
| `PATCH /v1/me` | `{first_name?, last_name?, email?}`: `null` yoki yo'q = o'zgartirmaslik, `""` = emailni o'chirish |
| `POST /v1/me/password` | `{current_password?, new_password}` -> 204 (Telegram orqali kirganda joriy parol yo'q) |
| `GET /v1/tariffs` | Tariflar (`price_som`, limitlar, `ai_enabled`) |
| `GET /v1/pricing` | `{plan_credit_price_som}`: bitta reja narxi (`kind: plan_credit`) |

## 4. Biznes-reja

Forma maydonlari: `docs/openapi.json` dagi `PlanInput` (nomlar moliyaviy yadrodagi bilan bir xil).
Majburiy: `faoliyat_turi` (`ishlab_chiqarish`, `qishloq_xojaligi`, `savdo`, `xizmat`), `loyiha_nomi`, `loyiha_qiymati`, va `hajm` + `narx` **yoki** `mahsulotlar`.
Hisob-kitob "Asosiy shablon npv 10 yillik.xls" asosida (`docs/EXCEL_SHABLON_TAHLILI.md`). Yangi ixtiyoriy maydonlar (2026-11-10):
- `mahsulotlar`: 1-6 ta `{nomi, hajm, narx, olchov?, xomashyo_narx?}` (hajm: yillik, to'liq quvvatda). Berilsa `hajm`/`narx` shart emas.
- `xomashyo_narx` (yoki `tovar_xaridi`): 1 birlik uchun tovar/xomashyo narxi (mahsulot ichida ham). Berilmasa `tannarx_ulushi` (tushumdan %), u ham bo'lmasa faoliyat turiga qarab: savdo 75%, ishlab chiqarish 55%, qishloq xo'jaligi 40%, xizmat 15% (`urug_yem_narx`/`texnika_xarajat` kiritilsa 0%). Formada savdo uchun tovar narxi yoki ulushini so'rash tavsiya etiladi.
- `dokon_ijarasi`, `joy_ijarasi`, `transport_xarajat` (oylik), `yer_ijarasi`, `urug_yem_narx`, `texnika_xarajat` (yillik): jadvallarda alohida qator.
- `aylanma_kapital`, `sugurta`: o'z mablag'idan. Kredit olish xarajati = kreditning 2% (o'z mablag'idan, avtomatik).
- `boshqa_kommunal`: yillik summa. `elektr`, `gaz`, `suv`, `oqava`: oylik miqdor.
- `quvvat`: 10 ta foiz (0-150), standart 75, 77, 80, 82, 85, 90, 92, 95, 100, 100. `diskont`: foiz, standart 14.
- `kredit_turi` standarti endi `differensial` (shablondagidek).
- `jshshir`: 14 raqam, ixtiyoriy, qo'lda kiritiladi (faqat Word hujjatiga yoziladi).
- Muqova rasmi: `POST /v1/plans/images` (kirgan foydalanuvchi, multipart `file`, JPG/PNG, 5 MB gacha, 20/daq)
  -> 201 `{image_id}`; uni `PlanInput.rasm_id` ga yozing (faqat o'z rasmingiz ishlaydi). `rasm_avto` (standart `true`):
  rasm yuklanmasa faoliyat turiga mos rasm avtomatik qo'yiladi (server `PEXELS_API_KEY` yoki `PIXABAY_API_KEY` bo'lsa), ostida "Foto: muallif / manba" yozuvi. Xatolar: `bad_file`, `file_too_large`.
- `indicators` ga qo'shildi: `dpp`, `dscr_min`, `zararsizlik_nuqtasi` (%). `npv`/`irr`/`payback`/`dpp` sof pul oqimidan (soliq va kredit foizidan keyin).
- 2026-11-11: loyiha davri kredit muddatidan: `ceil(muddat / 12)` yil, 1..10 (36 oy -> 3 yil; muddat yo'q -> 10). `indicators.loyiha_yillari` (yangi maydon) shu davr; jadvallardagi yil ustunlari, `npv`/`irr`/`payback`/`dpp`/`roi` faqat shu yillar uchun. `quvvat` hali 10 ta qiymat qabul qiladi, ortiqchasi e'tiborsiz.
Noma'lum maydon yuborilsa 422. Ma'lumotnomalar: `GET /v1/meta/activity-types`, `GET /v1/meta/business-categories`.

| Metod va yo'l | Tavsif |
| --- | --- |
| `POST /v1/plans/preview` | Mehmon ham. Forma o'zgarganda (debounce 500 ms) jonli ko'rsatkichlar: `{indicators, tables, context}` |
| `POST /v1/plans` | `{input: PlanInput, use_ai: true}` -> 202 `PlanOut` (`status: queued`) |
| `GET /v1/plans?limit&offset` | Mening rejalarim |
| `GET /v1/plans/{id}` | Holat: `queued`, `running`, `done`, `failed` |
| `GET /v1/plans/{id}/download?format=docx`, `xlsx` yoki `pdf` | `{url, expires_in}`: 10 daqiqalik havola, `window.location.href = url`. PDF ixtiyoriy: `PlanOut.has_pdf` false bo'lsa 404 `pdf_unavailable` |

Oqim: `POST /v1/plans` -> har 2 soniyada `GET /v1/plans/{id}` (AI bilan 1 daqiqagacha cho'zilishi mumkin) ->
`done` bo'lsa yuklash tugmalari, `failed` bo'lsa xabar (kvota avtomatik qaytariladi).

## 5. Katalog

R2 bucket yopiq (2026-11-10): `preview_image` endi `r2.dev` havolasi emas, backend manzili `GET /v1/catalog/products/{id}/image` (302, 1 soatlik imzolangan havola, `Cache-Control: public, max-age=1800`). `<img src>` ga to'g'ridan-to'g'ri qo'yiladi. PDF faqat `GET .../download` (sotib olgan foydalanuvchi, 10 daqiqalik havola).

| Metod va yo'l | Tavsif |
| --- | --- |
| `GET /v1/catalog/categories` | `{key, label, icon, count}[]` |
| `GET /v1/catalog/products?category&q&limit&offset` | `{items, total, limit, offset}` |
| `GET /v1/catalog/products/{id yoki slug}` | Bitta mahsulot |
| `GET /v1/catalog/owned` | Kirgan foydalanuvchi sotib olgan rejalar: `{product_ids: string[]}` |
| `POST /v1/catalog/products/{id}/view` | Sahifa ochilganda bir marta, javobni kutmasdan |
| `GET /v1/catalog/products/{id}/download` | Sotib olgan bo'lsa `{url, expires_in}`, aks holda 403 `not_purchased` |

## 6. To'lovlar

| Metod va yo'l | Tavsif |
| --- | --- |
| `GET /v1/payments/methods` | `{click, payme, manual}`: faqat `true` lar uchun tugma ko'rsatiladi |
| `POST /v1/payments` | `{kind: subscription/catalog/plan_credit, target_id, provider: click/payme/manual}` -> `{payment, checkout}` |
| `GET /v1/payments` | Mening to'lovlarim |
| `GET /v1/payments/{id}` | Holat: `pending`, `reviewing`, `paid`, `cancelled`, `rejected` |
| `POST /v1/payments/{id}/receipt` | Qo'lda to'lov cheki (`file`: JPG/PNG/WEBP/PDF, 10 MB gacha) |

`target_id`: obuna uchun tarif kodi (`pro`, `enterprise`), katalog uchun mahsulot `id`, `plan_credit` uchun yuborilmaydi.
Narxni server hisoblaydi; frontend summani hech qachon yubormaydi.

- `checkout.type == "redirect"`: `window.location.href = checkout.url` (Click/Payme). To'lovdan keyin foydalanuvchi **`/tolov/{payment_id}`** ga qaytadi; sahifa har 3 soniyada `GET /v1/payments/{id}` ni so'raydi.
- `checkout.type == "manual"`: karta raqami, summa, ko'rsatma va chek yuklash formasi.

## 6.1 Aloqa formasi (2026-11-12)

| Metod va yo'l | Body | Javob |
| --- | --- | --- |
| `POST /v1/contact` | `{name(2-100), phone, topic: plan/payment/catalog/partnership/other, message(10-2000), website: ""}` | 201 `{id, status}` |

Token ixtiyoriy (bo'lsa murojaat foydalanuvchiga bog'lanadi). `website`: yashirin maydon, doim bo'sh yuboriladi (to'ldirilsa bot deb hisoblanadi, 201 qaytadi, saqlanmaydi). Cheklov: IP bo'yicha 10 daqiqada 5 ta, bitta raqamdan 60 soniyada 1 ta (429 `rate_limited`). Adminga Telegram xabari ketadi.

## 7. Admin (role = admin, 2FA majburiy)

| Metod va yo'l | Tavsif |
| --- | --- |
| `GET /v1/admin/stats` | Asosiy raqamlar (`messages_new`: javob kutayotgan murojaatlar, 2026-11-12) |
| `GET /v1/admin/payments?status&limit&offset` | To'lovlar navbati: `PaymentOut` + `user_id`, `user_phone`, `user_name`, `has_receipt` |
| `GET /v1/admin/payments/{id}/receipt` | Chekni ko'rish uchun 5 daqiqalik havola |
| `POST /v1/admin/payments/{id}/approve` va `/reject` | `{note?}` |
| `GET /v1/admin/users?q` | Foydalanuvchilar |
| `GET /v1/admin/catalog/products?q&category&active&limit&offset` | `{items, total, limit, offset}`: yashirilganlar ham (`AdminProductOut` = `ProductOut` + `is_active`, `file_key`) |
| `POST /v1/admin/catalog/products`, `PATCH /v1/admin/catalog/products/{id}` | Katalog boshqaruvi (`is_active: false` = yashirish). Javob `AdminProductOut`; noma'lum `category_key` -> 400 `bad_category` |
| `GET /v1/admin/messages?status=new/done&limit&offset` | Aloqa formasidan murojaatlar: `{id, name, phone, topic, message, status, admin_note, user_id, created_at}` |
| `POST /v1/admin/messages/{id}/done` | `{note?}`: javob berildi deb belgilash |

## 8. Frontend yaratishi shart bo'lgan sahifalar (backend shularga yo'naltiradi)

| Yo'l | Nima uchun |
| --- | --- |
| `/tolov/{payment_id}` | Click/Payme'dan qaytish |
| `/tg` | Telegram Mini App (bot tugmasi shu yerga ochadi) |
| `/tariflar` | `quota_exceeded` dagi `upgrade_url` |

## 9. Frontend xavfsizlik qoidalari

- `innerHTML` / `dangerouslySetInnerHTML` foydalanuvchi ma'lumoti bilan ishlatilmaydi.
- Token `localStorage`/`sessionStorage` ga yozilmaydi.
- API manzili build vaqtida `NEXT_PUBLIC_API_URL` dan olinadi.
- Fayl yuklash havolalari faqat API qaytargan `url` dan olinadi.

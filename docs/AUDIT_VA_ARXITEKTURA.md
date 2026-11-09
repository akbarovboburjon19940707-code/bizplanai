# BizplanAI: audit va 10 000 foydalanuvchiga mo'ljallangan arxitektura

Asl hujjat (rasmli): https://claude.ai/artifact/1ucG8qrjcYjJEpRCAaoHZX. Bu fayl uning matnli nusxasi va **joriy holat** ustuni bilan.

## 1. Xulosa
Tahlil qilingan `bizplanai_production_ready_latest_oxirgisi` (Flask, bitta `app.py`, SQLite, xotiradagi holat, lokal fayllar) bir nechta server
nusxasida ishlay olmasdi va pullik funksiyalari bo'sh edi. Eski `uzbiznesss_site` esa yangisidan boy chiqdi (haqiqiy AI, to'g'ri Telegram login,
katalog PDF'lari, Click/Payme). Yangi backend ikkalasining eng yaxshi qismlaridan **noldan** yozildi; moliyaviy yadro (`financial_engine`,
`word_generator`, `excel_generator`) o'zgarishsiz ko'chirildi (bitta reja ~0,4 s, ~37 KB).

"10 000 bir vaqtdagi foydalanuvchi" ≈ 1 000 API so'rov/s (har faol foydalanuvchi ~10 s da bitta so'rov). Haqiqiy tor joy: AI generatsiya
(LLM limiti), CPU emas.

## 2. Topilgan muammolar va holat

| # | Muammo (eski versiya) | Yangi backend'da |
| --- | --- | --- |
| 1 | `/save` limitni tekshirmasdi, mehmon cheksiz yuklardi | Hal: atomik kvota, generatsiya faqat kirgan foydalanuvchiga |
| 2 | Telegram `init_data` HMAC tekshirilmasdi | Hal: rasmiy algoritm + `auth_date` muddati; bot orqali kirish Redis'da bir martalik token |
| 3 | Katalog xaridi umumiy namuna berardi, egasi tekshirilmasdi | Hal: `entitlements`, haqiqiy PDF, imzolangan havola. **PDF'larni R2'ga ko'chirish qoldi** |
| 4 | Noma'lum mahsulot ID birinchi mahsulotga aylanardi | Hal: 404 |
| 5 | Soxta "Gemini AI" rasm va to'qilgan STIR ma'lumoti | Hal: olib tashlandi. Haqiqiy AI matn qaytarildi (kalit kerak). STIR: rasmiy manba yo'q |
| 6 | Kabinetda saqlangan XSS, token localStorage'da | Backend tomoni hal (httpOnly refresh). **Frontend qoidasi `AGENTS.md` 8-bo'lim** |
| 7 | Refresh token bekor qilinmasdi | Hal: bazada, aylanadi, qayta ishlatish aniqlanadi |
| 8 | Webhooklarda qator qulfi yo'q | Hal: `SELECT FOR UPDATE`, idempotent `mark_paid`, Postgres'da parallel testlar |
| 9 | Admin: bitta parol, 2FA yo'q, CSRF | Hal: rol + TOTP; token header'da (cookie emas), shuning uchun CSRF xavfi yo'q |
| 10 | Admin katalog tahriri xotirada | Hal: katalog Postgres'da |
| 11 | `requirements.txt` da `openpyxl` yo'q | Hal: qotirilgan versiyalar |
| 12 | `admin.html` mavjud bo'lmagan `admin.js` ni chaqirardi | Frontend qayta yoziladi |

Qo'shimcha topilmalar: `APP_ENV=development` bilan deploy xavfi (hal: production guard), AI generatsiya HTTP so'rov ichida ketma-ket va
2 sinxron worker (hal: navbat + parallel bo'limlar), ochiq R2 bucket (qoldi), maxfiy ma'lumotlar ZIP'larda (qoldi, CLAUDE.md "DARHOL").

## 3. Masshtablash to'siqlari va yechimlar

| To'siq | Yechim |
| --- | --- |
| SQLite | Render Postgres (+ PgBouncer kerak bo'lsa, o'qish replikasi) |
| Xotiradagi rate limit/sessiya/tokenlar | Redis (Render Key Value, `maxmemoryPolicy: noeviction`) |
| Lokal fayllar | Cloudflare R2, imzolangan URL |
| Sinxron generatsiya | arq navbat + worker nusxalari |
| `create_all()` | Alembic |
| Sahifalashsiz admin ro'yxatlar | `limit/offset` |
| Kuzatuv yo'q | JSON loglar, `X-Request-ID`, `/healthz`, `/readyz`, Sentry (DSN bo'lsa) |

## 4. Maqsadli arxitektura (Render)

```
Foydalanuvchi ─► Frontend (Static Site, CDN) ─► API (FastAPI, 2→8 nusxa, stateless)
                                                   ├─► Postgres 16
                                                   ├─► Key Value (Redis): navbat, kesh, rate limit, Telegram login
                                                   └─► Cloudflare R2: Word/Excel/PDF/cheklar
                                         Worker (arq, 2→6 nusxa): hisob + Word + Excel + AI ─► Postgres/R2/LLM
Click/Payme/Telegram ─► API (webhook)
```

## 5. Yuklama hisobi (taxminiy; k6 dan keyin tuzatiladi)

| Servis | Hisob | Boshlang'ich | Autoscaling |
| --- | --- | --- | --- |
| API | 1 000 RPS, nusxa ~250-400 RPS | 2-3 | 2→8, CPU 60% |
| Worker | cho'qqi 17 reja/s × 0,4 s ≈ 7 CPU | 2 | 2→6, CPU 70% |
| Postgres | 8×10 + 6×5 ≈ 110 ulanish | 1 | vertikal (+PgBouncer) |
| Key Value | navbat, kesh, kvota | 1 | vertikal |

Render cheklovi: autoscaling faqat Professional workspace'da; narxni Render pricing sahifasida hisoblang.
AI qaytarilganda bitta reja ~10-15 ming token (taxmin): daqiqasiga 1 000 reja 10-15 mln token. Arzon tarifda mumkin emas: shuning uchun
tarifga bog'langan AI + `AI_DAILY_TOKEN_BUDGET` + statik matnga avtomatik o'tish.

Qabul mezoni: k6 da 10 000 VU, p95 < 300 ms, xato < 0.1%, navbatda kutish < 30 s.

## 6. Reja
1. Barqarorlik (1-2 hafta): kritik muammolar, Postgres/R2/Redis, birinchi deploy. **Backend qismi bajarilgan, deploy qoldi.**
2. Parallel (3-5 hafta): yangi backend (bajarilgan) va yangi frontend (qoldi).
3. Yuklama va start (1-2 hafta): k6, autoscaling, alertlar, zaxira nusxa, trafikni o'tkazish.

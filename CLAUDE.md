# BizplanAI: loyiha konteksti (Claude Code uchun)

O'zbekiston tadbirkorlari uchun bank talablariga mos biznes-reja platformasi (Word + Excel, 10 yillik moliyaviy model,
ixtiyoriy AI matn, tayyor rejalar katalogi, Click/Payme to'lovlari, Telegram bot va Mini App).
**Maqsad: bir vaqtda 10 000 faol foydalanuvchiga xizmat ko'rsatadigan production tizim, Render.com da.**
Foydalanuvchi bilan o'zbek tilida (lotin) gaplash. Kod, o'zgaruvchi va commit xabarlari inglizcha.

## Rollar
- **Claude**: backend (`backend/`) va arxitektura.
- **Codex**: frontend (`frontend/`) va integratsiya/kod tekshiruvi. Topshiriq: `frontend/AGENTS.md`.
- **Gemini**: mustaqil tahlil va takliflar (kodga to'g'ridan-to'g'ri tegmaydi).
- Backend va frontend faqat `backend/docs/API_CONTRACT.md` + `backend/docs/openapi.json` orqali bog'lanadi.

## Holat (2026-11-10)
| Qism | Holat |
| --- | --- |
| Backend | **Tayyor**: FastAPI, 36 endpoint, 14 jadval, Alembic (0002: `refresh_tokens.replaced_by`). 27 test (SQLite 25), `ruff` toza. 2026-11-10: Click ikkinchi tranzaksiya xatosi to'langan obunani bekor qilardi (tuzatildi); refresh 30 s grace oynasi (bir vaqtdagi tablar). Bu ikkisi Postgres'da hali sinalmagan |
| Frontend | **1-bosqich** (Codex) va **3-bosqichning `/dashboard` + `/reja` qismi** (Claude, 2026-11-10): 5 bosqichli forma (RHF + Zod), 6 tagacha mahsulot, tovar narxi/ulushi, aylanma kapital, quvvat va diskont, jonli preview (500 ms debounce), sessionStorage qoralama, reja yaratish va holat. Haqiqiy backend bilan brauzerda sinalgan. Hali yo'q: 2-bosqich (`/kirish`, `/royxat`, `/kabinet`), unit/e2e testlar |
| Deploy | `backend/render.yaml` yozilgan, **Render'da hali yaratilmagan**. Frontend bloki `frontend/AGENTS.md` 6-bo'limda |
| Yuklama testi | `backend/loadtest/k6.js` yozilgan, **hali ishga tushirilmagan** (staging kerak) |

## Tuzilma
```
backend/    FastAPI + arq worker (README.md ni o'qi)
frontend/   Next.js 15 static export uchun topshiriq paketi (AGENTS.md)
docs/       AUDIT_VA_ARXITEKTURA.md (tahlil, 12 muammo, arxitektura, reja)
reference/old-uzbiznesss/   ESKI saytning Python kodi (AI, Click/Payme, PDF, R2). Faqat o'qish va ko'chirish uchun
scripts/sync_contract.py    OpenAPI ni qayta eksport qilib frontend/docs ga nusxalaydi
```

## Buyruqlar (backend/ ichida)
```bash
pip install -r requirements-dev.txt && cp .env.example .env
alembic upgrade head && python -m app.cli seed
uvicorn app.main:app --reload --port 8000        # /docs
pytest                                           # SQLite
TEST_DATABASE_URL=postgresql://u:p@localhost/db pytest   # Postgres (parallel testlar ham)
ruff check .
python -m app.cli create-admin --phone +998... --password '...'   # 2FA (TOTP) avtomatik
```

## Arxitektura qarorlari (qayta muhokama qilma, sabab bo'lmasa)
- **Modulli monolit** (mikroservis emas): `app/modules/{auth,users,billing,plans,catalog,payments,admin,telegram,files,meta}`.
- **API stateless**; holat Postgres + Redis + R2'da. Render API'ni 2→8, worker'ni 2→6 nusxagacha avtomatik ko'paytiradi.
- **Og'ir ish navbatda**: `POST /v1/plans` 202 qaytaradi, `arq` worker hisoblaydi, Word/Excel yaratadi, R2'ga yozadi. Prod'da `JOB_MODE=queue`.
- **Kvota atomik**: `UPDATE ... WHERE used < limit` (billing/service.py). Tartib: obuna → kredit (AI beradi) → bepul. Xatoda `refund_quota`.
- **Pul tiyinda butun son** (`*_tiyin`); API javobida butun so'm (`*_som`). Narxni server hisoblaydi.
- **Huquq berish faqat** `payments/service.py` dagi `mark_paid` da, `SELECT ... FOR UPDATE` ostida, idempotent. Webhook'lar `payment_events` ga yoziladi.
- **Auth**: access JWT 15 daq (xotirada), refresh token bazada (sha256), bir martalik, qayta ishlatilsa hamma sessiya yopiladi, httpOnly cookie. Admin: TOTP majburiy.
- **Fayllar** yopiq R2 bucket, imzolangan 10 daqiqalik havola. Dev'da lokal papka.
- **AI** (`app/ai`): kalit bo'lmasa o'chiq (statik matn). 6 bo'lim parallel, provayder zaxira tartibi Groq→OpenAI→DeepSeek→Claude→Gemini, kunlik token byudjeti Redis'da. **AI API kalitlari hozir yo'q**, keyin env'ga qo'shiladi (chat obunalari, ya'ni Claude Pro/ChatGPT/Gemini, API bermaydi).
- **Frontend**: Next.js static export, Render Static Site (CDN). Katalog sahifalari build vaqtida yaratiladi.
- `APP_ENV=production` da noto'g'ri sozlamada server ishga tushmaydi (config.py `_production_guard`).

## Qoidalar
1. **Moliyaviy hisob-kitob manbai: `G:\Asosiy shablon npv 10 yillik.xls`** (tahlil: `docs/EXCEL_SHABLON_TAHLILI.md`, kod: `backend/app/engine/template_model.py`, test: `tests/test_template_model.py` Excel qiymatlari bilan). Formulani o'zgartirishdan oldin foydalanuvchidan so'ra va Excel moslik testini yashil saqla. 2026-11-10 gacha bo'lgan eski yadro formulalari (15% amortizatsiya, 60% tannarx va h.k.) o'rniga shu shablon olingan.
   **Word hujjati** bank shabloni asosida: `app/engine/word_template.py` + `templates/biznes_reja.docx` (`scripts/build_word_template.py` bilan yasaladi; qo'lda tahrirlamang). Tahlil: `docs/WORD_SHABLON_TAHLILI.md`. Har o'zgarishdan keyin hujjat Word'da ochilishini tekshiring.
2. API shakli o'zgarsa: avval kod, keyin `python scripts/sync_contract.py`, `backend/docs/API_CONTRACT.md` ni yangila. Buzuvchi o'zgarish (maydon o'chirish/nomini o'zgartirish) uchun foydalanuvchidan so'ra.
3. Har yangi endpoint/biznes qoidasi uchun test. Parallel/pul bilan bog'liq mantiq Postgres'da ham sinalsin.
4. Sxema o'zgarishi faqat Alembic migratsiyasi orqali (`alembic revision --autogenerate`, keyin qo'lda tekshir).
5. Maxfiy qiymatlarni kodga, logga, javobga yozma. `.env` git'ga kirmaydi.
6. Frontend yozuvchisi `frontend/docs/CONTRACT_REQUESTS.md` ga yozgan narsalarni ko'rib chiq va backend'da hal qil.

## DARHOL qilinadigan ishlar (foydalanuvchi bajaradi, sen eslat)
Eski loyiha ZIP'larida haqiqiy maxfiy ma'lumotlar bo'lgan va ular boshqa joylarga yuborilgan bo'lishi mumkin:
1. Click va Payme maxfiy kalitlarini kabinetlardan **qayta yaratish** (eski `providers/*/.env.local` da edi).
2. Barcha JWT/SECRET_KEY, admin parolini yangilash; Mongo/DB parollari.
3. Telegram bot tokenini @BotFather orqali qayta yaratish (agar ZIP'larda bo'lgan bo'lsa).
4. Katalogdagi 269 PDF turgan Cloudflare R2 bucket hozir **ochiq** (`r2.dev`): Public Access ni o'chirish. Unda eski saytning `generated/` (mijoz hujjatlari) ham bor. Yangi backend tayyor (rasm va PDF imzolangan havola bilan). Yopilgach eski jonli saytda katalog rasmlari ko'rinmaydi (PDF yuklab olish ishlaydi: S3 API orqali).
5. Eski GitHub repo (`uzbiznesss_site`, 112 commit) tarixida maxfiy fayl bo'lsa, repo'ni private qilish yoki tarixni tozalash.
6. Mijozlarning chek rasmlari/foydalanuvchi bazasi ZIP'larda edi: kelajakda bunday fayllarni arxivga qo'shma.

## Keyingi ishlar (ustuvorlik bo'yicha)
| # | Ish | Izoh |
| --- | --- | --- |
| 1 | Render staging: blueprint, R2, Postgres, Redis; Click/Payme/Telegram sinov | `backend/README.md` "Render'ga chiqarish". Click/Payme callback manzillari u yerda |
| 2 | Frontend 1-7 bosqichlar | `frontend/AGENTS.md`; har bosqichdan keyin integratsiya tekshiruvi |
| 3 | k6 yuklama testi (staging), natijaga qarab nusxa sonlari | Maqsad: p95 < 300 ms, xato < 0.1%, generatsiya navbatida kutish < 30 s |
| 4 | Eski ma'lumotlarni ko'chirish skripti | `reference/old-uzbiznesss/database.py` sxemasi → yangi jadvallar (users, payments, subscriptions). Parol xeshlari formati farq qiladi: tekshir |
| 5 | PDF eksport | Eski `modules/document_engine.py` LibreOffice orqali; Dockerfile'ga `libreoffice-writer` qo'shish va worker vazifasi qilish |
| 6 | Katalog PDF'larini R2 ga ko'chirish va `file_key` larni tekshirish | `app/cli.py seed` kalit: `catalog/pdfs/<id>.pdf` |
| 7 | Eski saytdan qolgan funksiyalar | `credit_calculator.py`, `financial_analysis.py`, `excel_model_editor.py`: kerak bo'lsa modul sifatida |
| 8 | STIR bo'yicha korxona ma'lumoti | Faqat rasmiy manba bilan; eski versiyadagi to'qima ma'lumot ishlatilmasin |
| 9 | Sentry, alertlar, zaxira nusxa, `/readyz` monitoring | |

## Ochiq biznes savollari (foydalanuvchidan so'ra, o'zing qaror qilma)
- Tariflar to'g'rimi: Bepul 3/kun-10/oy; Standart 50 000 so'm 15/50 (AI bilan); Premium 500 000 so'm 50/500. Bitta reja 50 000 so'm.
- Katalog minimal narxi 25 000 so'm (eski saytdagi qoida) saqlansinmi?
- Oylik AI byudjeti (kalit olingach `AI_DAILY_TOKEN_BUDGET` shunga qarab).
- Click/Payme shartnomalari holati; hozircha qo'lda karta to'lovi ishlaydi (`MANUAL_CARD_NUMBER`).
- R2 bucket'da 269 PDF haqiqatan bormi (eski `reference/old-uzbiznesss/` dagi `tmp/check_r2_files.py` g'oyasi bilan tekshirish).

## Eski sayt (reference/old-uzbiznesss) qanday ishlatiladi
Flask, `app.py` ~3000 qator. Foydali joylari: `modules/ai_engine.py` (promptlar, allaqachon ko'chirilgan), `modules/payment_service/` (Click/Payme, ko'chirilgan),
`modules/document_engine.py` (PDF), `modules/r2_storage.py`, `modules/telegram_notifier.py`, `database.py` (eski sxema).
**Koddan to'g'ridan-to'g'ri nusxa ko'chirma**: avval xavfsizlik va async moslik tekshirilsin.
`modules/payment.py` da biznes karta raqami qattiq yozilgan: yangi tizimda u faqat `MANUAL_CARD_NUMBER` env'dan olinadi.

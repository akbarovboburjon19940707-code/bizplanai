# BizplanAI backend (FastAPI)

Biznes-reja platformasining API va worker qismi. Frontend alohida (Next.js, Codex yozadi);
ular `docs/API_CONTRACT.md` va `docs/openapi.json` orqali bog'lanadi.

| Qism | Joyi | Izoh |
| --- | --- | --- |
| API | `app/main.py`, `app/modules/*` | 36 endpoint, yagona xato formati |
| Worker | `app/workers/settings.py` | arq: reja generatsiyasi, ko'rishlar hisobi, eskirgan to'lovlarni yopish |
| Moliyaviy yadro | `app/engine/` | Avvalgi versiyadan o'zgarishsiz |
| AI | `app/ai/` | Eski saytdan: 6 bo'lim, 5 provayder zaxirasi; kalit bo'lmasa o'chiq |
| To'lovlar | `app/modules/payments/` | Click, Payme, qo'lda karta + chek |
| Baza | `app/models/`, `alembic/` | 14 jadval, Postgres 16 |

## Lokal ishga tushirish

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
python -m app.cli seed                     # tariflar + 269 katalog mahsuloti
python -m app.cli create-admin --phone +998901234567 --password 'kamida-12-belgi'
uvicorn app.main:app --reload --port 8000  # http://localhost:8000/docs
```

Dev rejimida Redis kerak emas va reja so'rovning o'zida yaratiladi (`JOB_MODE=inline`).

## Testlar

```bash
pytest                                                          # SQLite
TEST_DATABASE_URL=postgresql://user:pass@localhost/test pytest  # Postgres (parallel kvota va to'lov testlari ham)
ruff check .
```

## Render'ga chiqarish

1. Cloudflare R2'da **yopiq** bucket yarating; katalog PDF'larini `catalog/pdfs/<mahsulot_id>.pdf` kalitiga ko'chiring.
   Hozirgi ochiq `r2.dev` bucket'ni yoping (fayl nomini bilgan har kim pulsiz yuklay oladi).
2. Render: New > Blueprint > shu repo. `render.yaml` API, worker, Postgres va Key Value'ni yaratadi.
3. `bizplan-secrets` guruhiga kalitlarni kiriting. **Eski ZIP'larda sizgan kalitlarni emas, kabinetlardan yangidan yaratilganlarini.**
4. Deploydan keyin API Shell'ida: `python -m app.cli create-admin --phone ... --password ...`, chiqqan `otpauth://` havolani Google Authenticator'ga qo'shing.
5. Telegram: `python scripts/set_telegram_webhook.py https://api.bizplanai.uz`
6. Merchant kabinetlarida callback manzillari:
   - Click Prepare: `https://api.bizplanai.uz/v1/payments/click/prepare`
   - Click Complete: `https://api.bizplanai.uz/v1/payments/click/complete`
   - Payme endpoint: `https://api.bizplanai.uz/v1/payments/payme` (hisob maydoni `order_id`)
7. DNS: `api.bizplanai.uz` -> `bizplan-api`.
8. Staging'da yuklama testi: `k6 run -e API=https://... loadtest/k6.js`.

`APP_ENV=production` da server noto'g'ri sozlama bilan (SQLite, Redis yo'q, zaif SECRET_KEY) ishga tushmaydi.

## Biznes qoidalari (tasdiqlang)

Hozirgi saytdan olingan; `app/cli.py` dagi `TARIFFS` yoki `tariffs` jadvalida o'zgartiriladi:

- Bepul: kuniga 3, oyiga 10 reja, AI'siz. Standart: 50 000 so'm/30 kun, 15/50, AI bilan. Premium: 500 000 so'm/30 kun, 50/500, AI bilan.
- Bitta reja (`plan_credit`): 50 000 so'm, AI bilan. Kredit bepul limitdan oldin sarflanadi.
- Katalog narxi kamida 25 000 so'm (hozirgi saytdagi qoida).
- To'lanmagan to'lovlar 24 soatdan keyin avtomatik bekor qilinadi.

## Hali qilinmagan

- PDF eksport (eski saytda LibreOffice orqali): Docker image'ga LibreOffice qo'shib, worker vazifasi sifatida.
- STIR bo'yicha korxona ma'lumoti: rasmiy manba ulanguncha olib tashlangan.
- Eski saytlardagi foydalanuvchi va to'lovlarni ko'chirish skripti.

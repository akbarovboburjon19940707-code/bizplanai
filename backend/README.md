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

To'liq yo'riqnoma: **`docs/DEPLOY.md`** (GitHub, staging va production Blueprint'lari, DNS, sinovlar, o'tish kuni).
Blueprint'lar repo ildizida: `render.staging.yaml` (eski sayt bilan parallel), `render.production.yaml` (o'tish kuni).
CI: `.github/workflows/ci.yml` (ruff, pytest SQLite + Postgres 16, frontend build, Docker image).

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

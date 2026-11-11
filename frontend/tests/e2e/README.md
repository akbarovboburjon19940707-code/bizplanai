# E2E testlar (Playwright)

Haqiqiy backend va shu backend'ga qarshi build qilingan statik sayt bilan ishlaydi (mock yo'q).
CI'da `.github/workflows/ci.yml` dagi `e2e` job aynan shu qadamlarni bajaradi.

## Lokal ishga tushirish
1. Backend (`backend/` ichida), CI'dagi env bilan (SQLite, `JOB_MODE=inline`, `STORAGE_BACKEND=local`,
   `TELEGRAM_BOT_TOKEN=123456:TEST`, `TELEGRAM_WEBHOOK_SECRET=e2e+secret/=`, `MANUAL_CARD_NUMBER=...`,
   `LOADTEST_TOKEN=<32+ belgi>`; testlarga xuddi shu qiymat `E2E_LOADTEST_TOKEN` sifatida):
   ```bash
   alembic upgrade head && python -m app.cli seed
   # xarid testi uchun "qoy-sotib-olish-biznes-rejasi" rejasining PDF'i kerak (fayli yo'q reja sotilmaydi):
   # ci.yml dagi "Backend: o'rnatish" qadamidagi kichik Python blokini ishga tushiring
   python -m app.cli create-admin --phone +998901110000 --password 'admin-e2e-pass-123'   # chiqqan secret= ni oling
   uvicorn app.main:app --port 8000
   ```
2. Frontend (`frontend/` ichida):
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000 NEXT_PUBLIC_SITE_URL=http://localhost:3000 npm run build
   npm run serve:static            # out/ ni Render kabi beradi (/tolov/* rewrite bilan)
   E2E_ADMIN_TOTP_SECRET=<secret> npm run e2e
   ```

`E2E_ADMIN_TOTP_SECRET` berilmasa admin bilan bog'liq testlar o'tkazib yuboriladi.
Testlar bitta bazani bo'lishadi va ketma-ket ishlaydi; har test o'z foydalanuvchisini yaratadi.
Telegram tashqarida taqlid qilinadi: bot "Start" webhook orqali, Mini App esa haqiqiy algoritm bilan imzolangan
`initData` va soxta SDK skripti bilan (backend imzoni o'zi tekshiradi).

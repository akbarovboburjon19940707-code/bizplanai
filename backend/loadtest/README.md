# Yuklama testi (k6)

Maqsad (CLAUDE.md): 10 000 faol foydalanuvchi, o'qish so'rovlari p95 < 300 ms, xato < 0.1%,
reja navbatda kutish + generatsiya p95 < 30 s.

## Tayyorlov
1. k6 o'rnating: https://grafana.com/docs/k6/latest/set-up/install-k6/ (Windows: `winget install k6`).
2. Kalit: Render → Environment Groups → `bizplan-stg-secrets` → `LOADTEST_TOKEN` (Blueprint o'zi yaratadi).
   Bu kalit bilan IP bo'yicha rate limit o'tkazib yuboriladi: test bitta kompyuterdan ketadi, haqiqiy
   foydalanuvchilar esa har biri o'z IP'sidan. Kalit **faqat staging'da** bor (production'da CI testi buni tekshiradi).

## Profillar
```bash
# 1) Tekshiruv (1.5 daqiqa, 5 VU): skript va muhit ishlayaptimi
k6 run -e API=https://api-yangi.bizplanai.uz -e TOKEN=<LOADTEST_TOKEN> -e PROFILE=smoke backend/loadtest/k6.js

# 2) Sig'im: bitta API nusxasi (staging: 1 x starter) qayerda sekinlashadi. 50 -> 800 VU, 15 daqiqa
k6 run -e API=https://api-yangi.bizplanai.uz -e TOKEN=<LOADTEST_TOKEN> -e PROFILE=capacity backend/loadtest/k6.js

# 3) Maqsad: 10 000 VU. Faqat production o'lchamidagi muhitda (8 API / 6 worker), kuchli mashinadan
k6 run -e API=... -e TOKEN=... -e PROFILE=target backend/loadtest/k6.js
```

Har tashrif: katalog sahifasi, kategoriyalar, bitta reja, tariflar; formani to'ldirish (3 ta `preview`);
har 10-tashrifda ro'yxat + kabinet. Alohida oqim daqiqasiga N ta reja yaratib, tayyor bo'lguncha kutadi
(`plan_ready_ms`). Production API'ga `-e ALLOW_PROD=1` siz yuborilmaydi.

## Natijani o'qish
- `http_req_duration{kind:read}` p95: katalog va kabinet; `{kind:preview}` p95: jonli hisob (chegara 800 ms).
- `plan_ready_ms` p95: navbat + generatsiya. Oshsa worker nusxasi yoki `max_jobs` ko'paytiriladi.
- **capacity** profilida p95 300 ms dan oshgan bosqichdagi VU soni = bitta nusxa sig'imi.
  10 000 / shu son = kerakli API nusxalari (render.production.yaml dagi `maxInstances: 8` bilan solishtiring).
- Postgres ulanishlari tugasa API loglarida `QueuePool limit` chiqadi: docs/DEPLOY.md, ulanish byudjeti.

Test ro'yxatdan o'tkazgan foydalanuvchilar (ismi `k6`, `k6-reja`) staging bazasida qoladi.

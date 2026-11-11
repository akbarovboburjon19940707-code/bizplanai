# Deploy yo'riqnomasi: GitHub + Render (eski sayt bilan parallel)

Maqsad: yangi sayt eski `bizplanai.uz` ga tegmasdan **staging**da ishlaydi, sinovdan o'tadi, keyin bir kunda o'tiladi.

| Muhit | Blueprint | Frontend | API | To'lovlar | Telegram |
| --- | --- | --- | --- | --- | --- |
| Eski sayt | (o'zgarmaydi) | `bizplanai.uz` | o'zi | Click/Payme (asosiy) | asosiy bot |
| Staging (yangi) | `render.staging.yaml` | `yangi.bizplanai.uz` | `api-yangi.bizplanai.uz` | faqat qo'lda karta | **test bot** |
| Production (yangi) | `render.production.yaml` | `bizplanai.uz`, `www` | `api.bizplanai.uz` | Click/Payme | asosiy bot |

Nega bunday: bitta Click/Payme merchant hisobida **bitta** callback manzili, bitta Telegram botda **bitta** webhook bo'ladi.
Ular o'tish kunigacha eski saytda qoladi.

## 0. Oldindan (bir marta)
- [ ] R2 `bizplanai-files` da Public Development URL o'chirilgan (2026-11-10 bajarilgan, `r2.dev` 401 qaytaradi).
- [ ] Eski ZIP'larda sizgan kalitlar yangilangan (CLAUDE.md "DARHOL"). Yangi tizimga faqat **yangi** kalitlar kiritiladi.

## 1. GitHub (private repo)
1. https://github.com/new: nomi `bizplanai-v2`, **Private**, README/.gitignore/litsenziya **qo'shmang**.
2. Loyiha papkasida:
   ```bash
   git remote add origin https://github.com/<login>/bizplanai-v2.git
   git push -u origin main
   ```
3. (Ixtiyoriy, GitHub Pro/Team kerak) Settings > Branches > `main` himoyasi: "Require status checks". Bepul tarifda private repo uchun yo'q.
4. Actions bo'limida CI yashil bo'lishini kuting. Backend job testlarni **Postgres 16** da ham ishga tushiradi
   (to'lov va kvota uchun parallel testlar faqat Postgres'da ishlaydi).

Repo'da `.env`, kalit va token yo'q (tarix tekshirilgan). `reference/` da eski sayt kodi bor: repo **private** bo'lishi shart.

## 2. Kalitlar (staging uchun)
| Kalit | Qayerdan |
| --- | --- |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | Cloudflare > R2 > Manage API tokens > Create: **Object Read & Write**, faqat `bizplanai-files` bucket'iga |
| `R2_BUCKET` | `bizplanai-files` |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_NAME` | @BotFather > `/newbot` (masalan `bizplanai_test_bot`): **asosiy bot emas** |
| `TELEGRAM_ADMIN_CHAT_ID` | admin xabarlari ketadigan chat ID |
| `MANUAL_CARD_NUMBER`, `MANUAL_CARD_HOLDER` | staging'da haqiqiy pul olinmasin desangiz bo'sh qoldiring yoki sinov kartasi |
| `PIXABAY_API_KEY` | `backend/.env` dagi kalit |
| AI kalitlari, `SENTRY_DSN` | ixtiyoriy (bo'sh: AI o'chiq, standart matn) |

`SECRET_KEY` va `TELEGRAM_WEBHOOK_SECRET` Render tomonidan avtomatik yaratiladi.

## 3. Render (staging)
1. Render > New > **Blueprint** > GitHub repo'ni ulang > **Blueprint path: `render.staging.yaml`**.
2. Yaratiladi: `bizplan-stg-api` (web), `bizplan-stg-worker`, `bizplan-stg-kv` (Redis), `bizplan-stg-db` (Postgres 16),
   `bizplan-stg-web` (static frontend). Narxlarni Render pricing sahifasida tekshiring (frontend static: bepul).
3. Apply. Render guruhda `sync: false` ni qo'llab-quvvatlamaydi, shuning uchun Blueprint guruhga faqat `SECRET_KEY` va
   `TELEGRAM_WEBHOOK_SECRET` ni yaratadi. Qolgan kalitlarni (2-bo'lim jadvali, `render.staging.yaml` oxiridagi ro'yxat)
   Dashboard > Environment Groups > `bizplan-stg-secrets` da **qo'lda** qo'shing; keyingi sync'lar ularni o'chirmaydi.
4. Birinchi deployda `preDeployCommand` migratsiya va katalogni (269 reja, 3 tarif) yozadi; qayta deployda takrorlamaydi.

## 4. DNS (Cloudflare, `bizplanai.uz` zonasi)
Render > servis > Settings > Custom Domains sahifasida ko'rsatilgan manzilga CNAME:

| Nom | Turi | Qiymat | Proxy |
| --- | --- | --- | --- |
| `yangi` | CNAME | `bizplan-stg-web.onrender.com` | DNS only (kulrang bulut) |
| `api-yangi` | CNAME | `bizplan-stg-api.onrender.com` | DNS only |

Render sertifikatni chiqargach (Custom Domains da "Verified"), xohlasangiz proxy'ni yoqish mumkin (SSL rejimi: Full (strict)).
Eski `bizplanai.uz` va `www` yozuvlariga **tegmang**.

## 5. Deploydan keyin
`bizplan-stg-api` > Shell:
```bash
python -m app.cli create-admin --phone +998XXXXXXXXX --password '<kuchli parol>'   # otpauth:// havolani Authenticator'ga
python scripts/set_telegram_webhook.py https://api-yangi.bizplanai.uz              # TEST bot uchun
```

## 6. Staging sinovlari (hammasi o'tmaguncha production yo'q)
- [ ] `https://api-yangi.bizplanai.uz/healthz` va `/readyz` 200
- [ ] `https://yangi.bizplanai.uz` ochiladi; javobda `X-Robots-Tag: noindex` bor
- [ ] Ro'yxatdan o'tish, sahifani yangilaganda sessiya saqlanadi (refresh cookie)
- [ ] `/dashboard`: jonli ko'rsatkichlar, reja yaratish, Word va Excel yuklab olish (Word'da muqova rasmi, jadvallar)
- [ ] Katalog: rasmlar `/v1/catalog/products/{id}/image` orqali ko'rinadi; sotib olinmagan PDF 403
- [ ] Katalog fayllari: `bizplan-stg-api` Shell'da `python -m app.cli check-catalog --report /tmp/katalog.csv`
      (PDF va muqova rasmi R2'da bormi). PDF'i yo'q reja sotilmaydi (`409 file_missing`, pul olinmaydi);
      ularni vaqtincha yashirish: `--hide-missing` (admin panel > Katalog > Yashirilgan, fayl yuklangach Ko'rsatish)
- [ ] Sentry: `SENTRY_DSN` qo'shilgan bo'lsa, xatolar `component=api` va `component=worker` belgisi bilan keladi
- [ ] Qo'lda to'lov: chek yuklash > admin tasdiqlaydi > huquq beriladi
- [ ] Test bot orqali kirish
- [ ] k6 yuklama testi: `k6 run -e API=https://api-yangi.bizplanai.uz backend/loadtest/k6.js` (maqsad: p95 < 300 ms, xato < 0.1%)

Frontend'da hali yo'q (o'tishdan oldin kerak): `/kirish`, `/royxat`, `/kabinet`, katalog va to'lov sahifalari (`frontend/AGENTS.md` 2, 4-bosqich).

## 7. O'tish kuni (production)
1. Eski saytdan ko'chirish (`python -m app.cli import-legacy`, yangi API Shell'ida; batafsil pastda, 9-bo'lim).
   Avval staging'da eski bazaning nusxasi bilan sinab ko'ring.
2. `production` branch'ini yarating (sinovdan o'tgan `main` holatidan): `git push origin main:production`.
   Keyin Render > New > Blueprint > `render.production.yaml` (staging bilan bir xil sinovlar).
3. Eski saytni faqat o'qish rejimiga o'tkazish (yangi to'lov qabul qilmasin), oxirgi ma'lumotlarni ko'chirish.
4. DNS: `bizplanai.uz`, `www` > `bizplan-web`; `api` > `bizplan-api`.
5. Click kabinet: Prepare `https://api.bizplanai.uz/v1/payments/click/prepare`, Complete `.../click/complete`;
   Payme: `https://api.bizplanai.uz/v1/payments/payme` (hisob maydoni `order_id`).
6. Asosiy bot: `python scripts/set_telegram_webhook.py https://api.bizplanai.uz` (production API Shell'ida).
7. Kuzatish: Render loglari, Sentry, birinchi haqiqiy to'lovni qo'lda tekshirish.

### 7.1 To'lovlarni ulash (Click servisi bitta: 100949; Payme kassasi bitta: uzbizness)
Ikkalasida ham callback manzili bitta, shuning uchun staging'da jonli sinov yo'q: ulash shu kuni.
1. **Oldindan**: eski sayt (Render) > Environment dan qiymatlarni **aynan** ko'chiring (foydalanuvchi qarori, 2026-11-11:
   o'tish kuni kalitlar almashtirilmaydi, Click operatori bilan alohida sinov qilinmaydi):
   `CLICK_SERVICE_ID=100949`, `CLICK_MERCHANT_ID`, `CLICK_MERCHANT_USER_ID`, `CLICK_SECRET_KEY`;
   Payme kassa ID > `PAYME_MERCHANT_ID`, kassa kaliti (eski `PAYME_KEY`) > `PAYME_SECRET_KEY`,
   `PAYME_CHECKOUT_URL=https://checkout.paycom.uz`. Kabinetlardagi hozirgi Prepare/Complete va Payme endpoint manzillarini
   yozib qo'ying (orqaga qaytish uchun).
2. Eski saytni faqat o'qish rejimiga o'tkazing (yuqoridagi 3-band) va shundan keyingina callback'larni almashtiring.
3. Click kabinet > Services > ✏️: Prepare/Complete manzillari (yuqoridagi 5-band). Payme kassa: endpoint, hisob maydoni `order_id`.
4. **Tekshiruv**: `/v1/payments/methods` > `click` va `payme` `true`. Har biridan bitta haqiqiy to'lov (masalan, katalog rejasi
   yoki kredit), kabinetda "Successfully"/"Оплачен", saytda huquq berilgani. Kerak bo'lsa kabinetdan qaytarish (Payme
   bekor qilish `CancelTransaction` orqali huquqni avtomatik qaytarib oladi).
5. Eski saytda o'tishdan oldin boshlangan, to'lanmagan buyurtmalar endi yopiladi (callback yangi API'ga keladi va
   ularni tanimaydi: Click -5, Payme -31050). Shuning uchun 3-band (faqat o'qish) to'lovlarni ulashdan oldin.
6. **O'tishdan 1-3 kun keyin, sayt barqaror bo'lgach: kalitlarni almashtirish** (eski kalitlar ZIP'larda bo'lgan; ular bilan
   pul o'g'irlab bo'lmaydi, lekin soxta "to'landi" callback'i bilan xizmatni tekin olish mumkin). Click kabinet > Services > ✏️ >
   yangi Secret key (kabinetda imkon bo'lmasa Click qo'llab-quvvatlashi orqali); darhol Render'da `CLICK_SECRET_KEY` > Save and deploy.
   Payme kassa > yangi kalit > `PAYME_SECRET_KEY`. Keyin bitta kichik to'lov bilan tekshiring. Eski sayt endi kerak emas,
   unga yangi kalit yozilmaydi.

**Orqaga qaytish:** DNS yozuvlarini va Click/Payme/Telegram manzillarini eski qiymatlarga qaytarish (eski servis o'chirilmaydi,
kamida 2 hafta zaxira sifatida turadi).

## 8. Production'ga chiqarish (o'tish kunidan keyin, har safar)
`main` ga push faqat **staging**ga chiqadi. Production servislari `production` branch'ini kuzatadi va faqat CI yashil
bo'lgan commit'ni deploy qiladi (`branch: production`, `autoDeployTrigger: checksPass`).

1. O'zgarish `main` da, CI yashil, staging'da tekshirilgan.
2. Chiqarish (faqat fast-forward, ya'ni staging'da sinalgan aynan o'sha commit):
   ```bash
   git fetch origin
   git push origin origin/main:production
   ```
3. Render `bizplan-api` > Events da deploy'ni kuzating; `https://api.bizplanai.uz/readyz` 200.

**Orqaga qaytarish:** Render > servis > Deploys > oldingi deploy > Rollback (tez), keyin `production` branch'ini tuzating.
Migratsiya orqaga qaytmaydi: sxemani buzuvchi o'zgarishlarni ikki bosqichda chiqaring (avval qo'shish, keyin o'chirish).

### Postgres ulanish byudjeti
`basic-1gb` da 100 ta ulanish bor (RAM 8 GB dan kam har qanday tarifda shu). `render.production.yaml` dagi
`DB_POOL_SIZE=3`, `DB_MAX_OVERFLOW=1` shu limitga moslangan: 22 jarayon x 4 = 88. Nusxa soni yoki `WEB_CONCURRENCY`
o'zgarsa `backend/tests/test_deploy_blueprints.py` CI'da xato beradi. k6 testida pool yetmasa (loglarda
`QueuePool limit ... reached`), pool'ni kattalashtirish o'rniga PgBouncer (transaction rejimi) qo'ying.

## 9. Eski saytdan ma'lumot ko'chirish
`backend/app/legacy_import.py`. Nimalar ko'chadi:
- foydalanuvchilar (telefon bo'yicha; mavjudlari qayta yaratilmaydi);
- faol pullik obunalar (`pro`, `enterprise`, muddati tugamaganlar);
- sotib olingan katalog rejalari: faqat egasi va reja **aniq** bo'lsa.

Eski parollar (Werkzeug xeshi) o'zgarishsiz ko'chadi: foydalanuvchi eski paroli bilan kiradi, kirish paytida xesh
yangi formatga o'tkaziladi. Eski Telegram hisoblari (telefon `tg_<id>`) telefonsiz va **parolsiz** ko'chadi, chunki
eski sayt ularga taxmin qilinadigan avtomatik parol qo'ygan. Ular Telegram orqali kiradi, xohlasa kabinetda parol
o'rnatadi. Eski adminlar oddiy foydalanuvchi bo'ladi: adminni `create-admin` (TOTP) bilan qayta yarating.

Manzilni Render Shell'ga joylashtirmang (joylashtirish belgilari va bufer chalkashligi xato beradi): eski baza
**External Database URL** ini API servisining Environment'iga `LEGACY_DATABASE_URL` sifatida qo'shing, ko'chirish
tugagach o'chiring.

```bash
# 1) Quruq yurish: hech narsa yozilmaydi, hisobot chiqadi
python -m app.cli import-legacy --report /tmp/legacy.csv
grep ',review,' /tmp/legacy.csv | cut -d, -f4 | cut -d: -f1 | sort | uniq -c   # sabablar (ism/telefonsiz)
# 2) Hisobotni ko'rib chiqing (review qatorlari), keyin yozing
python -m app.cli import-legacy --apply --report /tmp/legacy.csv
```

**Staging sinovi (2026-11-11, jonli eski baza):** 17 foydalanuvchi (13 yangi, 4 mavjud), 10 obuna (1 faol pullik
ko'chdi), 56 to'lov: 1 katalog xaridi ko'chdi, 10 tasi `review` ("egasi topilmadi": hisobsiz xarid, eski sayt
ro'yxatdan o'tmasdan sotgan; PDF xarid paytida berilgan, ko'chirilmaydi). `--apply` staging'da muvaffaqiyatli.

- **Ustunlar.** Jonli eski bazada `payments`: `id`, `user_id`, `user_name`, `project_name`, `product_id`,
  `payment_status`, `admin_status` va boshqalar (eski variant `payment_type` + `loyiha_nomi` ham qo'llab-quvvatlanadi).
  `users`: `id`, `phone`, `first_name`, ixtiyoriy `last_name`, `telegram_id`, `telegram_username`, `password_hash`,
  `role`, `is_active`, `created_at`; `subscriptions`: `id`, `user_id`, `plan_name`, `status`, `end_date`, ixtiyoriy `start_date`.
  Kerakli ustun bo'lmasa, skript mavjud ustunlarni ko'rsatib to'xtaydi. Jadval nomi boshqa bo'lsa: `--users-table`, `--subscriptions-table`, `--payments-table`.
- **Katalog xaridlari.** Reja `product_id` bo'yicha; to'langan = `payment_status=success` yoki `admin_status=approved`.
  Egasi `user_id`, telefon (istalgan yozuvda), Telegram id/username yoki yagona ism bo'yicha. Aniqlanmasa `review`.
- **Qayta ishga tushirish xavfsiz.** Obuna va huquqlar `lgs:` / `lgp:` belgilari bilan bir marta yoziladi.

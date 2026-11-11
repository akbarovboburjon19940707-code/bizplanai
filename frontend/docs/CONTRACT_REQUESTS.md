# Kontrakt so'rovlari (frontend -> backend)

Frontend'ga kerak, lekin kontraktda yo'q narsalar. Backend hal qilgach, shu yerdan o'chiriladi.

## 1. `PATCH /v1/me`: emailni o'chirib bo'lmaydi (2026-11-10, `/kabinet`)
- **Muammo:** `null` "o'zgartirmaslik" degani, `""` esa `EmailStr` tekshiruvidan o'tmaydi. Foydalanuvchi kiritgan emailni olib tashlay olmaydi.
- **Hozir frontend:** bo'sh email `null` bo'lib yuboriladi; saqlangach forma server javobi bilan yangilanadi (eski email qaytib chiqadi).
- **Taklif:** `email: ""` -> `NULL` (bo'sh satrni "o'chirish" deb qabul qilish). Javob shakli o'zgarmaydi.

## 2. `UserOut.has_password` (2026-11-10, `/kabinet` parol formasi)
- **Muammo:** Telegram orqali ro'yxatdan o'tgan foydalanuvchida parol yo'q, frontend buni bilmaydi va "Joriy parol" maydonini doim ko'rsatadi (izoh bilan: "Telegram orqali ... bo'sh qoldiring").
- **Taklif:** `UserOut` ga `has_password: bool` qo'shish (buzuvchi emas). Frontend `false` bo'lsa "Joriy parol" maydonini yashiradi.

## 3. Katalog: foydalanuvchi sotib olgan rejalar (2026-11-11, `/katalog/[slug]`)
- **Muammo:** "sotib olinganmi" degan maydon yo'q. Hozir egalik faqat "Sotib olish" bosilganda (`409 already_owned`)
  yoki "Avval sotib olganmisiz?" havolasi orqali yuklab olishga urinishda (`403 not_purchased`) bilinadi.
- **Taklif:** `GET /v1/catalog/owned` -> `{product_ids: string[]}` (kirgan foydalanuvchi). Frontend sahifa ochilganda
  bir marta so'raydi va darhol "Yuklab olish" tugmasini ko'rsatadi.

## 4. Bitta reja (`plan_credit`) narxi (2026-11-11, `/tariflar`)
- **Muammo:** `PLAN_CREDIT_PRICE_SOM` serverda, lekin API'da yo'q. Narxni kodga yozish taqiqlangan, shuning uchun
  `/tariflar` da "bitta reja sotib olish" kartasi hozircha ko'rsatilmaydi.
- **Taklif:** `GET /v1/payments/methods` yoki alohida `GET /v1/pricing` da `plan_credit_price_som` (buzuvchi emas).

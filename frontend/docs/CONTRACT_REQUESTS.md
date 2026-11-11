# Kontrakt so'rovlari (frontend -> backend)

Frontend'ga kerak, lekin kontraktda yo'q narsalar. Backend hal qilgach, shu yerdan o'chiriladi.

Hozircha ochiq so'rov yo'q.

## Hal qilinganlar (2026-11-11)
- `PATCH /v1/me`: `email: ""` emailni o'chiradi (`null` = o'zgartirmaslik).
- `UserOut.has_password`: Telegram orqali ro'yxatdan o'tganlarda `false`, `/kabinet` "Parol o'rnatish" ko'rsatadi.
- `GET /v1/catalog/owned` -> `{product_ids}`: mahsulot sahifasida darhol "Yuklab olish".
- `GET /v1/pricing` -> `{plan_credit_price_som}`: `/tariflar` da "Bitta reja" kartasi.

# Kontrakt so'rovlari (frontend -> backend)

Frontend'ga kerak, lekin kontraktda yo'q narsalar. Backend hal qilgach, shu yerdan o'chiriladi.

## 1. `PATCH /v1/me`: emailni o'chirib bo'lmaydi (2026-11-10, `/kabinet`)
- **Muammo:** `null` "o'zgartirmaslik" degani, `""` esa `EmailStr` tekshiruvidan o'tmaydi. Foydalanuvchi kiritgan emailni olib tashlay olmaydi.
- **Hozir frontend:** bo'sh email `null` bo'lib yuboriladi; saqlangach forma server javobi bilan yangilanadi (eski email qaytib chiqadi).
- **Taklif:** `email: ""` -> `NULL` (bo'sh satrni "o'chirish" deb qabul qilish). Javob shakli o'zgarmaydi.

## 2. `UserOut.has_password` (2026-11-10, `/kabinet` parol formasi)
- **Muammo:** Telegram orqali ro'yxatdan o'tgan foydalanuvchida parol yo'q, frontend buni bilmaydi va "Joriy parol" maydonini doim ko'rsatadi (izoh bilan: "Telegram orqali ... bo'sh qoldiring").
- **Taklif:** `UserOut` ga `has_password: bool` qo'shish (buzuvchi emas). Frontend `false` bo'lsa "Joriy parol" maydonini yashiradi.

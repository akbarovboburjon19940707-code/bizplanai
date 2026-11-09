"""Word shabloni uchun faoliyat turiga qarab matnlar va jadval ma'lumotlari.

Asl shablon matnlari faqat ishlab chiqarishga moslangan edi (docs/WORD_SHABLON_TAHLILI.md).
Matnlarda {loyiha_nomi}, {tashabbuskor}, {manzil}, {mahsulot} o'rniga qiymat qo'yiladi.
SWOT ro'yxatlari word_generator.generate_swot_and_market_analysis dan olinadi.
"""

COMMON_TALAB = (
    "O‘rganish natijalari shuni ko‘rsatmoqdaki, loyihaning ijobiy tomonlaridan biri rejalashtirilgan "
    "mahsulot va xizmatlarga yil davomida aholi va tadbirkorlar tomonidan barqaror talab mavjudligidir. "
    "Bu loyihani to‘liq amalga oshirish imkonini beradi."
)

TEXTS: dict[str, dict] = {
    "ishlab_chiqarish": {
        "soha_nomi": "ishlab chiqarish",
        "bino_turi": "Ishlab chiqarish binosi",
        "maqsad": [
            "Bugungi kunda Respublikamizda {loyiha_nomi} kabi ishlab chiqarish loyihalarini tashkil etish borasida bir "
            "qator yutuqlar qo‘lga kiritilmoqda. Buning asosiy omili mahalliy va xorijiy investitsiyalarning muntazam "
            "jalb etilishi, zamonaviy uskunalar bilan jihozlangan, import o‘rnini bosuvchi mahsulot ishlab chiqaruvchi "
            "korxonalarning tashkil etilayotganidir.",
            "{tashabbuskor} mazkur loyihani amalga oshirish natijasida hududda ishlab chiqarish faoliyatini "
            "rivojlantiradi, zamonaviy texnologiyalarni jalb etib raqobatbardosh mahsulot ishlab chiqaradi va "
            "quyidagi ijtimoiy-iqtisodiy natijalarga erishadi:",
        ],
        "resurs": "Tadbirkor tomonidan {mahsulot} ishlab chiqarish uchun xomashyo bazasi o‘rganilganda, asosiy xomashyo "
                  "mahalliy bozorda mavjudligi aniqlandi. Bu import o‘rnini bosuvchi, arzon va sifatli mahsulot ishlab "
                  "chiqarish imkoni borligidan dalolat beradi.",
        "raqobat": [
            "Bugungi kunda {manzil} hududida {mahsulot} ishlab chiqaruvchi korxonalar soni cheklangan va mahsulotlarning "
            "bir qismi qo‘shni tuman va viloyatlardan keltirilmoqda. Demak, korxona uchun asosiy raqobatchilar asosan "
            "qo‘shni hududlardagi ishlab chiqaruvchilar bo‘ladi.",
            "Boshqa hududlardan keltiriladigan mahsulotlar narxiga yo‘l haqi, vositachi foydasi va boshqa xarajatlar "
            "qo‘shiladi. Bu mahalliy ishlab chiqaruvchiga narx bo‘yicha ustunlik beradi.",
        ],
        "ekologiya": "{manzil} hududida rejalashtirilgan ishlab chiqarish faoliyati atrof-muhitga salbiy ta’siri kam "
                     "bo‘lgan faoliyat turlaridan hisoblanadi. Ishlab chiqarish jarayonida asosan tabiiy va xavfsiz "
                     "xomashyo hamda materiallardan foydalaniladi.",
        "p4": {
            "product": "Sifatli, standartlarga mos mahsulot: {mahsulot}.",
            "price": "Narx xomashyo tannarxi, raqobatchilar narxi va xaridorlar talabidan kelib chiqib belgilanadi; "
                     "ulgurji xaridorlarga chegirmalar ko‘zda tutilgan.",
            "place": "Ishlab chiqarish va sotish {manzil} hududida tashkil etiladi; mahsulot ulgurji xaridorlar, "
                     "do‘konlar va bozorlar orqali yetkaziladi.",
            "promotion": "{tashabbuskor} ijtimoiy tarmoqlar, mahalliy reklama, ulgurji xaridorlar bilan to‘g‘ridan-to‘g‘ri "
                         "shartnomalar va ko‘rgazmalar orqali mahsulotni targ‘ib qiladi.",
        },
        "segments": [
            {"nomi": "Ulgurji xaridorlar", "tavsif": "Ulgurji savdo korxonalari va distribyutorlar", "ulush": "40%",
             "geo": "{manzil}", "talab": "Ko‘payadi", "xarid": "Yuqori", "jalb": "Barqaror sifat, ulgurji narx"},
            {"nomi": "Chakana savdo", "tavsif": "Do‘konlar va savdo shoxobchalari", "ulush": "45%",
             "geo": "{manzil}", "talab": "Ko‘payadi", "xarid": "O‘rta", "jalb": "Arzon narx, sifat"},
            {"nomi": "Korporativ mijozlar", "tavsif": "Tashkilotlar va boshqa korxonalar", "ulush": "15%",
             "geo": "Viloyat va qo‘shni hududlar", "talab": "Barqaror", "xarid": "Yuqori", "jalb": "Shartnoma asosida yetkazish"},
        ],
    },
    "qishloq_xojaligi": {
        "soha_nomi": "qishloq xo‘jaligi",
        "bino_turi": "Xo‘jalik hududi",
        "maqsad": [
            "Aholi sonining o‘sishi va oziq-ovqat xavfsizligini ta’minlash vazifasi qishloq xo‘jaligiga zamonaviy "
            "texnologiyalarni jalb etishni taqozo etmoqda. {loyiha_nomi} loyihasi hududda yuqori hosildorlikka ega "
            "mahsulot yetishtirish va aholini sifatli, tabiiy mahsulot bilan ta’minlashga qaratilgan.",
            "{tashabbuskor} mazkur loyihani amalga oshirish natijasida yer va suv resurslaridan samarali foydalanadi "
            "hamda quyidagi ijtimoiy-iqtisodiy natijalarga erishadi:",
        ],
        "resurs": "Loyiha uchun zarur urug‘lik, yem, o‘g‘it va boshqa resurslar mahalliy bozorda mavjud. Xo‘jalik "
                  "hududidagi yer-suv sharoitlari {mahsulot} yetishtirish uchun qulay.",
        "raqobat": [
            "{manzil} hududida {mahsulot} yetishtiruvchi xo‘jaliklar mavjud bo‘lsa-da, sifatli va barqaror hajmdagi "
            "mahsulotga talab taklifdan yuqori. Asosiy raqobatchilar hududdagi fermer va dehqon xo‘jaliklaridir.",
            "Zamonaviy agrotexnologiyalar va mahsulotni bevosita xaridorga yetkazish xo‘jalikka narx va sifat "
            "bo‘yicha ustunlik beradi.",
        ],
        "ekologiya": "{manzil} hududida rejalashtirilgan qishloq xo‘jaligi faoliyatida yer va suv resurslaridan "
                     "agrotexnik qoidalarga muvofiq foydalaniladi; o‘g‘it va o‘simliklarni himoya qilish vositalari "
                     "belgilangan me’yorlarda qo‘llaniladi.",
        "p4": {
            "product": "Ekologik toza va sifatli qishloq xo‘jaligi mahsuloti: {mahsulot}.",
            "price": "Narx mavsum, bozor narxlari va xaridorlar bilan oldindan tuzilgan shartnomalar asosida belgilanadi.",
            "place": "Mahsulot {manzil} hududidagi xo‘jalikda yetishtiriladi va bozorlar, qayta ishlovchi korxonalar "
                     "hamda ulgurji xaridorlarga yetkaziladi.",
            "promotion": "{tashabbuskor} agroklasterlar, qayta ishlovchilar va ulgurji xaridorlar bilan shartnomalar, "
                         "ijtimoiy tarmoqlar va bozorlarda bevosita sotish orqali mahsulotni targ‘ib qiladi.",
        },
        "segments": [
            {"nomi": "Qayta ishlovchilar", "tavsif": "Agroklasterlar va qayta ishlash korxonalari", "ulush": "40%",
             "geo": "Viloyat", "talab": "Ko‘payadi", "xarid": "Yuqori", "jalb": "Shartnoma asosida barqaror hajm"},
            {"nomi": "Ulgurji xaridorlar", "tavsif": "Dehqon bozorlari va ulgurji savdogarlar", "ulush": "45%",
             "geo": "{manzil}", "talab": "Ko‘payadi", "xarid": "O‘rta", "jalb": "Sifat, mavsumiy narx"},
            {"nomi": "Aholi", "tavsif": "Bevosita iste’molchilar", "ulush": "15%",
             "geo": "{manzil}", "talab": "Barqaror", "xarid": "O‘rta", "jalb": "Tabiiy va yangi mahsulot"},
        ],
    },
    "savdo": {
        "soha_nomi": "savdo",
        "bino_turi": "Savdo do‘koni",
        "maqsad": [
            "Iste’mol tovarlari savdosi aholining kundalik ehtiyojlarini qondirishda muhim o‘rin tutadi. {loyiha_nomi} "
            "loyihasi hududda aholi uchun qulay xarid muhitini yaratish va keng turdagi sifatli tovarlarni maqbul "
            "narxlarda yetkazib berishga qaratilgan.",
            "{tashabbuskor} mazkur loyihani amalga oshirish natijasida savdo xizmatlari sifatini oshiradi va "
            "quyidagi ijtimoiy-iqtisodiy natijalarga erishadi:",
        ],
        "resurs": "Savdo uchun zarur tovarlar mahalliy ishlab chiqaruvchilar va ulgurji yetkazib beruvchilardan "
                  "xarid qilinadi; yetkazib beruvchilar bozori yetarli va raqobatli.",
        "raqobat": [
            "{manzil} hududida {mahsulot} savdosi bilan shug‘ullanuvchi tadbirkorlar mavjud, ammo aholi gavjum "
            "joylarda keng assortiment va qulay xizmatga talab yuqori. Asosiy raqobatchilar hududdagi do‘konlar va "
            "savdo tarmoqlaridir.",
            "Tovarlarni ishlab chiqaruvchilardan bevosita xarid qilish, qulay joylashuv va xizmat sifati korxonaga "
            "narx va xaridorlar oqimi bo‘yicha ustunlik beradi.",
        ],
        "ekologiya": "{manzil} hududida rejalashtirilgan savdo faoliyati atrof-muhitga sezilarli ta’sir "
                     "ko‘rsatmaydi; tovarlarni saqlash va sotishda sanitariya-gigiyena talablariga rioya qilinadi.",
        "p4": {
            "product": "Keng assortimentdagi sifatli tovarlar: {mahsulot}.",
            "price": "Narx xarid narxi va o‘rtacha savdo ustamasi asosida, raqobatchilar narxini hisobga olib "
                     "belgilanadi; doimiy xaridorlarga chegirmalar beriladi.",
            "place": "Savdo {manzil} hududidagi do‘konda, aholi gavjum va transport uchun qulay joyda tashkil etiladi.",
            "promotion": "{tashabbuskor} peshtaxta va vitrina bezagi, ijtimoiy tarmoqlar, aksiyalar va bonus tizimi "
                         "orqali xaridorlarni jalb etadi.",
        },
        "segments": [
            {"nomi": "Aholi", "tavsif": "Hududdagi oilalar va kundalik xaridorlar", "ulush": "70%",
             "geo": "{manzil}", "talab": "Ko‘payadi", "xarid": "O‘rta", "jalb": "Qulay joy, keng assortiment"},
            {"nomi": "Kichik biznes", "tavsif": "Kafe, oshxona va boshqa korxonalar", "ulush": "20%",
             "geo": "{manzil}", "talab": "Ko‘payadi", "xarid": "Yuqori", "jalb": "Ulgurji narx, yetkazib berish"},
            {"nomi": "Tashkilotlar", "tavsif": "Davlat va xususiy tashkilotlar", "ulush": "10%",
             "geo": "Tuman va viloyat", "talab": "Barqaror", "xarid": "Yuqori", "jalb": "Shartnoma asosida ta’minot"},
        ],
    },
    "xizmat": {
        "soha_nomi": "xizmat ko‘rsatish",
        "bino_turi": "Xizmat ko‘rsatish binosi",
        "maqsad": [
            "Xizmat ko‘rsatish sohasi iqtisodiyotning eng tez rivojlanayotgan tarmoqlaridan biridir. {loyiha_nomi} "
            "loyihasi hududda aholi va tadbirkorlarga zamonaviy, tezkor va sifatli xizmat ko‘rsatishni tashkil "
            "etishga qaratilgan.",
            "{tashabbuskor} mazkur loyihani amalga oshirish natijasida hududda xizmatlar sifati va qamrovini "
            "oshiradi hamda quyidagi ijtimoiy-iqtisodiy natijalarga erishadi:",
        ],
        "resurs": "Xizmat ko‘rsatish uchun zarur uskunalar va sarf materiallari mahalliy bozorda mavjud; malakali "
                  "mutaxassislarni jalb qilish imkoniyati yetarli.",
        "raqobat": [
            "{manzil} hududida {mahsulot} xizmatini ko‘rsatuvchi korxonalar mavjud, ammo sifatli va tezkor xizmatga "
            "talab ortib bormoqda. Asosiy raqobatchilar hududdagi xususiy xizmat ko‘rsatuvchilardir.",
            "Zamonaviy uskunalar, malakali xodimlar va mijozlarga individual yondashuv korxonaga sifat va "
            "xizmat tezligi bo‘yicha ustunlik beradi.",
        ],
        "ekologiya": "{manzil} hududida rejalashtirilgan xizmat ko‘rsatish faoliyati atrof-muhitga salbiy ta’siri "
                     "juda kam bo‘lgan faoliyat turlaridan hisoblanadi.",
        "p4": {
            "product": "Sifatli va kafolatlangan xizmat: {mahsulot}.",
            "price": "Xizmat narxi tannarx, raqobatchilar narxi va mijozlar talabidan kelib chiqib belgilanadi; "
                     "doimiy mijozlarga imtiyozlar beriladi.",
            "place": "Xizmat {manzil} hududidagi qulay joylashgan binoda ko‘rsatiladi.",
            "promotion": "{tashabbuskor} ijtimoiy tarmoqlar, onlayn buyurtma, tavsiyalar va bonus dasturlari orqali "
                         "mijozlarni jalb etadi.",
        },
        "segments": [
            {"nomi": "Aholi", "tavsif": "Hududdagi jismoniy shaxslar", "ulush": "70%",
             "geo": "{manzil}", "talab": "Ko‘payadi", "xarid": "O‘rta", "jalb": "Sifat, qulay narx"},
            {"nomi": "Tadbirkorlar", "tavsif": "Kichik va o‘rta biznes subyektlari", "ulush": "20%",
             "geo": "{manzil}", "talab": "Ko‘payadi", "xarid": "Yuqori", "jalb": "Tezkorlik, shartnoma"},
            {"nomi": "Tashkilotlar", "tavsif": "Davlat va xususiy tashkilotlar", "ulush": "10%",
             "geo": "Tuman va viloyat", "talab": "Barqaror", "xarid": "Yuqori", "jalb": "Abonent xizmati"},
        ],
    },
}

RISKS = [
    ("Bozor va raqobat riski", "Narx siyosatini moslashtirish, assortimentni kengaytirish, sifat nazorati."),
    ("Moliyaviy risk (to‘lovlar kechikishi)", "Aylanma mablag‘ zaxirasi, oldindan to‘lov tizimi, xarajatlarni nazorat qilish."),
    ("Xomashyo va tovar narxlari o‘sishi", "Uzoq muddatli ta’minot shartnomalari, muqobil yetkazib beruvchilar."),
    ("Kadrlar riski", "Malaka oshirish, munosib ish haqi va rag‘batlantirish tizimi."),
    ("Tashqi omillar (tabiiy ofat, tariflar)", "Mol-mulkni sug‘urtalash, energiya tejamkor uskunalar."),
]

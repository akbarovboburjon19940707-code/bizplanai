"""Word hujjati: faoliyat turi bo'yicha bozor tahlili va SWOT ma'lumotlari + shablon asosidagi generator.

Hujjatning o'zi bank shabloni asosida yaratiladi: app/engine/word_template.py (docs/WORD_SHABLON_TAHLILI.md).
"""


def generate_swot_and_market_analysis(ctx: dict) -> dict:
    """
    Kiritilgan soha (faoliyat_turi) va loyiha parametrlari asosida
    O'zbekiston banklari (Xalq banki, Mikrokreditbank, Agrobank) talablariga mos
    chuqur bozor tahlili va 2x2 SWOT matritsasini dinamik shakllantiradi.
    """
    faoliyat_turi = (ctx.get("faoliyat_turi") or "ishlab_chiqarish").strip().lower()
    loyiha_nomi = ctx.get("loyiha_nomi") or "Investitsiya loyihasi"
    tashabbuskor = ctx.get("tashabbuskor") or "Tashabbuskor Korxona"
    narx = float(ctx.get("narx") or 0)
    hajm = float(ctx.get("hajm") or 0)
    olchov = ctx.get("olchov") or "dona"
    manzil = ctx.get("manzil") or "O'zbekiston Respublikasi"

    swot_configs = {
        "ishlab_chiqarish": {
            "market_demand": (
                f"O'zbekiston Respublikasida mahalliy ishlab chiqaruvchilarni qo'llab-quvvatlash va sanoat kooperatsiyasini "
                f"rivojlantirish davlat siyosatining ustuvor yo'nalishi hisoblanadi. «{tashabbuskor}» tomonidan amalga oshirilayotgan "
                f"«{loyiha_nomi}» loyihasi ichki bozorda import o'rnini bosuvchi sifatli mahsulot ishlab chiqarish, "
                f"mahalliy xomashyoni chuqur qayta ishlash hamda {manzil} hududida yangi barqaror ish o'rinlarini yaratishga qaratilgan. "
                f"Hozirgi kunda ushbu mahsulot turiga bo'lgan yillik talab barqaror o'sib bormoqda va loyihaning 1-yildagi "
                f"rejalashtirilgan hajmi ({hajm:,.0f} {olchov}) bozor ehtiyojining muayyan qismini sifatli qoplash imkonini beradi."
            ),
            "advantages": [
                "Zamonaviy energiya tejamkor avtomatlashtirilgan uskunalar hisobiga mahsulot tannarxining 10-15% ga arzonligi;",
                "Mahalliy sifatli xomashyo yetkazib beruvchilar bilan to'g'ridan-to'g'ri uzoq muddatli shartnomalar;",
                "Mahsulot sifatining milliy (O'zDSt) va xalqaro texnik reglamentlarga to'liq mosligi;",
                "Qulay logistika tarmog'i va buyurtmachilarga tovarlarni o'z vaqtida yetkazib berish tizimi."
            ],
            "pricing": (
                f"Bozor tahlili natijalariga ko'ra, 1 {olchov} mahsulotning sotish narxi {narx:,.0f} so'm miqdorida "
                f"belgilangan bo'lib, bu amaldagi o'rtacha bozor narxlaridan 5-8% ga qulayroqdir. "
                f"Doimiy va ulgurji xaridorlar uchun 30% oldindan to'lov va qolgan qismini muddatli to'lash imkoniyati ko'zda tutilgan."
            ),
            "swot": {
                "strengths": [
                    "Zamonaviy yuqori unumli va energiya tejamkor texnologik liniyalar",
                    "Mahalliy xomashyo bazasining yaqinligi tufayli arzon transport xarajatlari",
                    "Tajribali boshqaruv tarkibi va malakali texnolog-mutaxassislar",
                    "Raqobatbardosh narx va qat'iy standartlashtirilgan sifat nazorati"
                ],
                "weaknesses": [
                    "Dastlabki oylarda brendning bozorda keng tanilish darajasining pastligi",
                    "Yangi ishga qabul qilinadigan xodimlarni texnologik liniyaga qayta tayyorlash",
                    "Ishlab chiqarish quvvatlarini to'liq o'zlashtirish uchun vaqt talabi"
                ],
                "opportunities": [
                    "Davlat tomonidan ishlab chiqarish korxonalariga berilayotgan soliq va bojxona imtiyozlari",
                    "Yirik sanoat korxonalari bilan kooperatsiya asosida yetkazib berish shartnomalari",
                    "Investitsiya davrida quvvatni 100% ga yetkazish va eksport bozorlariga chiqish",
                    "Yangi turdosh mahsulotlar nomenklaturasini bosqichma-bosqich kengaytirish"
                ],
                "threats": [
                    "Xomashyo va ehtiyot qismlar narxlarining mavsumiy tebranishi",
                    "Ichki bozorda yangi muqobil ishlab chiqaruvchilar sonining ortishi",
                    "Energiya resurslari va kommunal tariflarining kutilmagan o'sishi"
                ]
            }
        },
        "qishloq_xojaligi": {
            "market_demand": (
                f"Aholi sonining muntazam o'sishi va oziq-ovqat xavfsizligini ta'minlash vazifasi agrar sohaga zamonaviy texnologiyalarni "
                f"jalb etishni taqozo etmoqda. «{loyiha_nomi}» loyihasi {manzil} hududida yuqori hosildorlikka ega agromahsulotlar "
                f"yetishtirish, suv tejovchi ilg'or usullardan foydalanish va aholini toza, tabiiy mahsulot bilan ta'minlashga xizmat qiladi."
            ),
            "advantages": [
                "Resurs tejamkor (tomchilatib/yomg'irlatib) sug'orish agrotexnologiyasining tatbiq etilishi;",
                "Yuqori navli, kasalliklarga chidamli urug'lik va ko'chatlardan foydalanish;",
                "Ekologik toza va tabiiy o'g'itlar asosida yuqori sifatli qishloq xo'jaligi hosili;",
                "Mahsulotni yig'ishtirib olish va qayta ishlash zanjirining yo'lga qo'yilishi."
            ],
            "pricing": (
                f"Yetishtirilgan mahsulotning 1 {olchov} uchun sotish narxi {narx:,.0f} so'm qilib belgilangan. "
                f"Mavsumiy tebranishlarni hisobga olgan holda mahsulotning bir qismi agroklasterlar va ulgurji xaridorlarga "
                f"oldindan tuzilgan fyuchers shartnomalari orqali kafolatlangan narxlarda realizatsiya qilinadi."
            ),
            "swot": {
                "strengths": [
                    "Unumdor yer-suv resurslari va qulay tabiiy-iqlimiy sharoitlar",
                    "Suv tejovchi ilg'or texnologiyalar hisobiga tannarxning pastligi",
                    "Ekologik toza, tabiiy va yuqori xaridorgir qishloq xo'jaligi mahsuloti",
                    "Tajribali agronomlar va soha bo'yicha amaliy tajribaga ega xodimlar"
                ],
                "weaknesses": [
                    "Qishloq xo'jaligi ishlab chiqarishining tabiiy mavsumiylikka bog'liqligi",
                    "Hosilni uzoq muddat sifatli saqlash uchun maxsus sovutkichli omborlar talabi",
                    "Dastlabki davrda ekinlar hosildorligini moslashtirish bosqichining mavjudligi"
                ],
                "opportunities": [
                    "Agrosanoat klasterlari va qayta ishlovchi korxonalar bilan kafolatlangan xarid tizimi",
                    "Suv tejovchi texnologiyalarni joriy etish uchun davlat subsidiyalari va imtiyozli kreditlar",
                    "Mahsulotlarni saralash va qadoqlash orqali qo'shilgan qiymat yaratish",
                    "Qo'shni davlatlarga yangi qishloq xo'jaligi mahsulotlarini eksport qilish imkoniyati"
                ],
                "threats": [
                    "Kutilmagan noqulay ob-havo hodisalari (qurg'oqchilik, erta sovuq urishi)",
                    "Qishloq xo'jaligi zararkunandalari va o'simlik kasalliklari xavfi",
                    "Mavsum avjida bozorda taklifning keskin ko'payishi oqibatida narxlarning pasayishi"
                ]
            }
        },
        "savdo": {
            "market_demand": (
                f"Iste'mol tovarlari savdosi va chakana savdo tarmog'i aholining kundalik talabini qondirishda muhim o'rin tutadi. "
                f"«{loyiha_nomi}» loyihasi {manzil} hududida aholi uchun qulay xarid muhitini yaratish, keng turdagi sifatli tovarlarni "
                f"arzon va qulay sharoitlarda yetkazib berishga qaratilgan."
            ),
            "advantages": [
                "Aholi gavjum bo'lgan, transport qatnovi qulay va xarid 'traffic'i yuqori lokatsiya;",
                "Ishlab chiqaruvchilardan to'g'ridan-to'g'ri xarid qilish hisobiga vositachilik ustamasining yo'qligi;",
                "Zamonaviy avtomatlashtirilgan kassa va ombor hisobi (ERP/POS) tizimlari;",
                "Keng assortiment va mijozlarga moslashuvchan xizmat ko'rsatish madaniyati."
            ],
            "pricing": (
                f"Savdo faoliyatida o'rtacha ustama 15-20% oralig'ida belgilangan bo'lib, o'rtacha chek {narx:,.0f} so'm miqdorida baholangan. "
                f"Doimiy mijozlar uchun bonus kartalari va chegirma aksiyalari ko'zda tutilgan."
            ),
            "swot": {
                "strengths": [
                    "Xaridorlar oqimi yuqori bo'lgan qulay savdo lokatsiyasi",
                    "Ishlab chiqaruvchi zavodlar bilan to'g'ridan-to'g'ri uzoq muddatli ta'minot shartnomalari",
                    "Keng turdagi talabgir tovarlar assortimentining doimiy mavjudligi",
                    "Zamonaviy elektron to'lov va sodiqlik tizimlarining to'liq joriy etilganligi"
                ],
                "weaknesses": [
                    "Savdo aylanmasini yuqori darajada ushlab turish uchun aylanma mablag'larga katta talab",
                    "Savdo va ombor binolari ijarasiga bog'liqlik",
                    "Dastlabki oylarda mijozlar bazasini shakllantirish va marketing xarajatlari"
                ],
                "opportunities": [
                    "Onlayn buyurtma va yetkazib berish (e-commerce) xizmatini yo'lga qo'yish",
                    "Doimiy xaridorlar uchun maxsus keshbek va aksiyalar orqali savdoni oshirish",
                    "Boshqa tumanlarda yangi savdo nuqtalarini ochish orqali tarmoq kengaytirish",
                    "Ulgurji korporativ mijozlarga ta'minot xizmatini ko'rsatish"
                ],
                "threats": [
                    "Yirik chakana savdo tarmoqlari (supermarketlar) tomonidan kuchli raqobat",
                    "Tovarlarning yaroqlilik muddatlari va tovar yo'qotishlari xavfi",
                    "Aholi real daromadlari va xarid qobiliyatining o'zgarishi"
                ]
            }
        },
        "xizmat": {
            "market_demand": (
                f"Xizmat ko'rsatish sohasi zamonaviy iqtisodiyotning eng tez rivojlanayotgan tarmog'idir. "
                f"«{loyiha_nomi}» loyihasi {manzil} hududida aholi va tadbirkorlik sub'ektlariga yuqori darajadagi zamonaviy, "
                f"tezkor va kafolatlangan xizmat ko'rsatishni tashkil etishga yo'naltirilgan."
            ),
            "advantages": [
                "Mijozlarga individual yondashuv va yuqori xizmat ko'rsatish madaniyati;",
                "Zamonaviy texnik jihozlar va malakali sertifikatlangan mutaxassislar;",
                "Onlayn bronlash, masofaviy murojaat va qulay to'lov usullarining mavjudligi;",
                "Bozor talablariga mos raqobatbardosh va adolatli narx siyosati."
            ],
            "pricing": (
                f"Ko'rsatiladigan asosiy xizmatlar tarifi o'rtacha {narx:,.0f} so'm miqdorida shakllantirilgan. "
                f"Korporativ mijozlar uchun uzoq muddatli servis shartnomalari va abonent to'lovi tizimi joriy qilinadi."
            ),
            "swot": {
                "strengths": [
                    "Mijozlarga qaratilgan professional xizmat ko'rsatish va individual yondashuv",
                    "Zamonaviy innovatsion uskunalar va dasturiy ta'minotdan foydalanish",
                    "Buyurtmalarni tezkor qabul qilish va xizmat sifatiga kafolat berish tizimi",
                    "Qulay transport lokatsiyasi va mijozlar uchun barcha qulayliklar mavjudligi"
                ],
                "weaknesses": [
                    "Xizmat sifatining xodimlar malakasi va mas'uliyatiga bevosita bog'liqligi",
                    "Boshlang'ich bosqichda mijozlar ishonchini qozonish uchun marketing xarajatlari",
                    "Xizmat quvvatlarining ish boshida to'liq band bo'lmaslik ehtimoli"
                ],
                "opportunities": [
                    "Hududda sifatli ixtisoslashtirilgan xizmatlarga o'sib borayotgan ehtiyoj",
                    "B2B korporativ mijozlar bilan uzoq muddatli abonent shartnomalarini tuzish",
                    "Mobil ilova va ijtimoiy tarmoqlar orqali yangi mijozlar oqimini jalb etish",
                    "Turdosh xizmatlar spektrini bosqichma-bosqich kengaytirib borish"
                ],
                "threats": [
                    "Xizmat ko'rsatish bozorida yangi xususiy o'yinchilarning paydo bo'lishi",
                    "Malakali mutaxassislarning rotatsiyasi (kadrlar o'zgaruvchanligi)",
                    "Mijozlarning xizmat ko'rsatish sifatiga bo'lgan talabchanligining oshishi"
                ]
            }
        }
    }

    config = swot_configs.get(faoliyat_turi, swot_configs["ishlab_chiqarish"])
    return {
        "market_demand": config["market_demand"],
        "advantages": config["advantages"],
        "pricing": config["pricing"],
        "swot": config["swot"],
    }


def generate_word_report(model_data: dict, output_path: str, ai_sections: dict | None = None,
                         image: bytes | None = None, image_credit: str | None = None) -> str:
    """Biznes-reja Word hujjati: bank shabloni asosida (app/engine/word_template.py)."""
    from app.engine.word_template import render_plan_docx

    return render_plan_docx(model_data, output_path, ai_sections, image, image_credit)

"""
UzBizness / BizplanAI — Professional Word (.docx) Biznes-Reja Generatori
O'zbekiston tijorat banklari (Xalq banki, Mikrokreditbank, Agrobank, Biznesni rivojlantirish banki)
talablariga to'liq moslashtirilgan 12+ bo'limli keng qamrovli investitsion biznes-reja shabloni.
"""

import os
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


NAVY_COLOR = RGBColor(30, 58, 138)       # #1E3A8A
DARK_GRAY_COLOR = RGBColor(55, 65, 81)   # #374151
LIGHT_BG_HEX = "F1F5F9"                  # Och kulrang jadval sarlavhasi
HEADER_BG_HEX = "1E3A8A"                # To'q ko'k jadval sarlavhasi
TOTAL_BG_HEX = "FEF3C7"                 # Sariq yig'indi foni


def _set_cell_background(cell, hex_color: str):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def _set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="D1D5DB"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="1E3A8A"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def generate_swot_and_market_analysis(ctx: dict) -> dict:
    """
    Kiritilgan soha (faoliyat_turi) va loyiha parametrlari asosida
    O'zbekiston banklari (Xalq banki, Mikrokreditbank, Agrobank) talablariga mos
    chuqur bozor tahlili va 2x2 SWOT matritsasini dinamik shakllantiradi.
    """
    faoliyat_turi = (ctx.get("faoliyat_turi") or "ishlab_chiqarish").strip().lower()
    faoliyat_nomi = ctx.get("faoliyat_turi_nomi") or "Ishlab chiqarish"
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
                    "10 yillik investitsiya davrida quvvatni 100% ga yetkazish va eksport bozorlariga chiqish",
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


def generate_word_report(model_data: dict, output_path: str) -> str:
    ctx = model_data.get("context", {})
    ind = model_data.get("indicators", {})
    tables = model_data.get("tables", [])
    faoliyat_turi = ctx.get("faoliyat_turi", "ishlab_chiqarish")
    faoliyat_nomi = ctx.get("faoliyat_turi_nomi", "Ishlab chiqarish")
    loyiha_nomi = ctx.get("loyiha_nomi") or "Investitsiya loyihasi"
    tashabbuskor = ctx.get("tashabbuskor") or "Tashabbuskor Korxona"

    # Dinamik chuqur bozor va SWOT tahlilini olamiz
    analysis = generate_swot_and_market_analysis(ctx)
    swot = analysis["swot"]

    doc = Document()

    # Sahifa maydonlari (Margins)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

        # Header & Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run(f"Biznes-reja: «{loyiha_nomi}» | 10 yillik moliyaviy model")
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(156, 163, 175)

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run(f"«{tashabbuskor}» — Maxfiy tijorat hujjati. Faqat bank va investorlar uchun.")
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(156, 163, 175)

    # ════════════════════════════════════════════════════════════
    # TITUL SAHIFASI
    # ════════════════════════════════════════════════════════════
    tp0 = doc.add_paragraph()
    tp0.paragraph_format.space_before = Pt(80)

    tp_title = doc.add_paragraph()
    tp_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = tp_title.add_run("BIZNES-REJA\n")
    r_t.bold = True
    r_t.font.size = Pt(26)
    r_t.font.color.rgb = NAVY_COLOR

    r_sub = tp_title.add_run(f"«{loyiha_nomi.upper()}»\n")
    r_sub.bold = True
    r_sub.font.size = Pt(18)
    r_sub.font.color.rgb = RGBColor(31, 41, 55)

    r_desc = tp_title.add_run(f"{faoliyat_nomi} sohasida faoliyatni kengaytirish va yangi ish o'rinlari yaratish bo'yicha 10 yillik investitsion loyiha")
    r_desc.font.size = Pt(12)
    r_desc.font.italic = True
    r_desc.font.color.rgb = RGBColor(107, 114, 128)

    doc.add_paragraph().paragraph_format.space_before = Pt(100)

    # Titul rekvizitlar bloki
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Tashabbuskor:", tashabbuskor),
        ("Rahbar:", ctx.get("fio") or "—"),
        ("Xizmat ko'rsatuvchi bank:", ctx.get("bank") or "Tijorat banki"),
        ("Kredit talabi:", f"{ctx.get('kredit', 0):,.0f} so'm ({ctx.get('foiz', 14)}% yillik, {ctx.get('muddat', 120)} oy)"),
        ("Sana va manzil:", f"{datetime.now().strftime('%d.%m.%Y')} yil, {ctx.get('manzil') or 'O`zbekiston'}"),
    ]
    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.5)
        p0 = c0.paragraphs[0].add_run(label)
        p0.bold = True
        p0.font.size = Pt(10.5)
        p1 = c1.paragraphs[0].add_run(val)
        p1.font.size = Pt(10.5)

    doc.add_page_break()

    # ════════════════════════════════════════════════════════════
    # MUNDARIJA
    # ════════════════════════════════════════════════════════════
    h_toc = doc.add_heading("MUNDARIJA", level=1)
    h_toc.runs[0].font.color.rgb = NAVY_COLOR

    toc_items = [
        "1. LOYIHA PASPORTI VA REZYUMESI",
        "2. LOYIHANING MAQSADI VA VAZIFALARI",
        "3. BOZOR TAHLILI VA MARKETING STRATEGIYASI",
        "4. SWOT TAHLILI (KUCHLI VA ZAIF TOMONLAR)",
        "5. ISHLAB CHIQARISH / XIZMAT KO'RSATISH JARAYONI VA REJASI",
        "6. RISKLARNI BAHOLASH VA ULARNI BOSHQARISH REJASI",
        "7. TASHKILIY VA BOSHQARUV TUZILMASI (KADRLAR)",
        "8. 10 YILLIK MOLIYAVIY HISOB-KITOBLAR VA SAMARADORLIK",
        "9. XULOSA VA BANK KAFOLATLARI",
        "10. ILOVALAR (1-14 MOLIYAVIY JADVALLAR TO'PLAMI)",
    ]
    for item in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(item)
        run.font.size = Pt(11)
        run.font.bold = True

    doc.add_page_break()

    # ════════════════════════════════════════════════════════════
    # 1. LOYIHA PASPORTI
    # ════════════════════════════════════════════════════════════
    h1 = doc.add_heading("1. LOYIHA PASPORTI VA REZYUMESI", level=1)
    h1.runs[0].font.color.rgb = NAVY_COLOR

    p_lead = doc.add_paragraph()
    p_lead.add_run(
        f"Mazkur biznes-reja «{tashabbuskor}» tomonidan «{loyiha_nomi}» loyihasini "
        f"amalga oshirish, ishlab chiqarish/xizmat ko'rsatish quvvatlarini zamonaviy texnologiyalar asosida "
        f"jihozlash hamda tijorat banki kredit mablag'laridan samarali foydalanish maqsadida ishlab chiqilgan."
    )

    passport_items = [
        ("Loyiha nomi", loyiha_nomi),
        ("Tashabbuskor korxona", tashabbuskor),
        ("Mulkchilik shakli", ctx.get("mulk") or "MCHJ"),
        ("STIR (INN)", ctx.get("stir") or "—"),
        ("Rahbar F.I.O.", ctx.get("fio") or "—"),
        ("Xizmat ko'rsatuvchi bank", ctx.get("bank") or "Tijorat banki"),
        ("Faoliyat sohasi", faoliyat_nomi),
        ("Loyiha umumiy qiymati", f"{ctx.get('loyiha_qiymati', 0):,.0f} so'm (100%)"),
        ("Tashabbuskorning o'z mablag'i", f"{ctx.get('oz_mablag', 0):,.0f} so'm"),
        ("So'ralayotgan bank krediti", f"{ctx.get('kredit', 0):,.0f} so'm ({ctx.get('foiz', 14)}% yillik)"),
        ("Kredit muddati va imtiyozli davr", f"{ctx.get('muddat', 120)} oy (shundan {ctx.get('imtiyoz', 12)} oy imtiyozli davr)"),
        ("Sof joriy qiymat (NPV, 10 yil)", f"{ind.get('npv', 0):,.0f} so'm"),
        ("Ichki daromadlilik normasi (IRR)", f"{ind.get('irr', 0):.1f}%"),
        ("Investitsiyalarning rentabelligi (ROI)", f"{ind.get('roi', 0):.1f}%"),
        ("O'zini oqlash muddati (Payback)", f"{ind.get('payback', 0):.1f} yil"),
        ("Yangi yaratiladigan ish o'rinlari", f"{int(ctx.get('xodim', 0)) + int(ctx.get('yangi_xodim', 0)) + int(ctx.get('direktor', 1))} ta"),
    ]

    p_tbl = doc.add_table(rows=1, cols=2)
    p_tbl.style = "Table Grid"
    _set_table_borders(p_tbl)
    hdr = p_tbl.rows[0].cells
    hdr[0].text = "Ko'rsatkich nomi"
    hdr[1].text = "Loyiha parametrlari"
    _set_cell_background(hdr[0], HEADER_BG_HEX)
    _set_cell_background(hdr[1], HEADER_BG_HEX)
    hdr[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    hdr[1].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    hdr[0].paragraphs[0].runs[0].bold = True
    hdr[1].paragraphs[0].runs[0].bold = True

    for k, v in passport_items:
        row = p_tbl.add_row().cells
        _set_cell_margins(row[0])
        _set_cell_margins(row[1])
        row[0].text = str(k)
        row[1].text = str(v)
        row[0].paragraphs[0].runs[0].font.size = Pt(10)
        row[1].paragraphs[0].runs[0].font.size = Pt(10)

    doc.add_page_break()

    # ════════════════════════════════════════════════════════════
    # 2. BOZOR TAHLILI VA MARKETING STRATEGIYASI
    # ════════════════════════════════════════════════════════════
    h2 = doc.add_heading("2. BOZOR TAHLILI VA MARKETING STRATEGIYASI", level=1)
    h2.runs[0].font.color.rgb = NAVY_COLOR

    doc.add_heading("2.1. Bozor hajmi va talab tahlili", level=2)
    doc.add_paragraph(analysis["market_demand"])

    doc.add_heading("2.2. Raqobat ustunliklari", level=2)
    for adv in analysis["advantages"]:
        p_adv = doc.add_paragraph(style='List Bullet')
        r_adv = p_adv.add_run(adv)
        r_adv.font.size = Pt(10.5)

    doc.add_heading("2.3. Narxlash va to'lov siyosati", level=2)
    doc.add_paragraph(analysis["pricing"])

    # ════════════════════════════════════════════════════════════
    # 3. SWOT TAHLILI (2x2 MATRITSA)
    # ════════════════════════════════════════════════════════════
    h3 = doc.add_heading("3. SWOT TAHLILI (2x2 STRATEGIK MATRITSA)", level=1)
    h3.runs[0].font.color.rgb = NAVY_COLOR

    doc.add_paragraph(
        f"«{loyiha_nomi}» loyihasining ichki salohiyati va tashqi bozor omillari tizimli 2x2 SWOT matritsasi "
        f"ko'rinishida baholandi:"
    )

    swot_tbl = doc.add_table(rows=0, cols=2)
    swot_tbl.style = "Table Grid"
    _set_table_borders(swot_tbl)

    STRENGTH_BG = "1E3A8A"    # To'q ko'k
    WEAKNESS_BG = "C2410C"    # To'q to'q sariq (Orange)
    OPPORTUNITY_BG = "0369A1" # Ochiq ko'k / Moviy
    THREAT_BG = "991B1B"      # To'q qizil

    # 1-Qator: Strengths & Weaknesses
    hdr_row_1 = swot_tbl.add_row().cells
    hdr_row_1[0].text = "KUCHLI TOMONLAR (STRENGTHS)"
    hdr_row_1[1].text = "ZAIF TOMONLAR (WEAKNESSES)"
    _set_cell_background(hdr_row_1[0], STRENGTH_BG)
    _set_cell_background(hdr_row_1[1], WEAKNESS_BG)
    for c in hdr_row_1:
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c.paragraphs[0].runs[0].bold = True

    body_row_1 = swot_tbl.add_row().cells
    body_row_1[0].text = "\n".join(f"• {item}" for item in swot["strengths"])
    body_row_1[1].text = "\n".join(f"• {item}" for item in swot["weaknesses"])
    _set_cell_margins(body_row_1[0])
    _set_cell_margins(body_row_1[1])

    # 2-Qator: Opportunities & Threats
    hdr_row_2 = swot_tbl.add_row().cells
    hdr_row_2[0].text = "IMKONIYATLAR (OPPORTUNITIES)"
    hdr_row_2[1].text = "XAVF-XATARLAR (THREATS)"
    _set_cell_background(hdr_row_2[0], OPPORTUNITY_BG)
    _set_cell_background(hdr_row_2[1], THREAT_BG)
    for c in hdr_row_2:
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c.paragraphs[0].runs[0].bold = True

    body_row_2 = swot_tbl.add_row().cells
    body_row_2[0].text = "\n".join(f"• {item}" for item in swot["opportunities"])
    body_row_2[1].text = "\n".join(f"• {item}" for item in swot["threats"])
    _set_cell_margins(body_row_2[0])
    _set_cell_margins(body_row_2[1])

    doc.add_page_break()

    # ════════════════════════════════════════════════════════════
    # 4. RISKLARNI BAHOLASH VA BOSHQARISH
    # ════════════════════════════════════════════════════════════
    h4 = doc.add_heading("4. RISKLARNI BAHOLASH VA ULARNI BOSHQARISH REJASI", level=1)
    h4.runs[0].font.color.rgb = NAVY_COLOR

    risk_tbl = doc.add_table(rows=1, cols=4)
    risk_tbl.style = "Table Grid"
    _set_table_borders(risk_tbl)
    rhdrs = ["Xavf-xatar turi", "Ehtimollik", "Ta'sir darajasi", "Xavfni kamaytirish va boshqarish choralari"]
    for idx, rh in enumerate(rhdrs):
        c = risk_tbl.rows[0].cells[idx]
        c.text = rh
        _set_cell_background(c, HEADER_BG_HEX)
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c.paragraphs[0].runs[0].bold = True

    risk_data = [
        ("Bozor va raqobat riski", "O'rta", "O'rta", "Moslashuvchan narx siyosati, mahsulot turlarini ko'paytirish, sifat nazorati"),
        ("Moliyaviy va to'lov riski", "Past", "Yuqori", "Oldindan to'lov tizimi (kamida 30-50%), qat'iy kassa intizomi, kreditni o'z vaqtida so'ndirish"),
        ("Xomashyo ta'minoti riski", "O'rta", "O'rta", "Bir nechta to'g'ridan-to'g'ri ishlab chiqaruvchilar bilan uzoq muddatli shartnomalar tuzish"),
        ("Operatsion va texnik risk", "Past", "Past", "Uskunalarga muntazam profilaktik xizmat ko'rsatish, malakali texnik mutaxassislarni jalb qilish"),
    ]
    for r in risk_data:
        rc = risk_tbl.add_row().cells
        for idx, val in enumerate(r):
            _set_cell_margins(rc[idx])
            rc[idx].text = val

    doc.add_page_break()

    # ════════════════════════════════════════════════════════════
    # 5. 10 YILLIK MOLIYAVIY JADVALLAR VA ILOVALAR
    # ════════════════════════════════════════════════════════════
    h5 = doc.add_heading("5. 10 YILLIK MOLIYAVIY HISOB-KITOBLAR VA ILOVALAR", level=1)
    h5.runs[0].font.color.rgb = NAVY_COLOR

    doc.add_paragraph(
        "Loyihaning moliyaviy hisob-kitoblari 10 yillik davr uchun xalqaro standartlar hamda "
        "O'zbekiston tijorat banklarining amaldagi me'yoriy talablariga mos ravishda tayyorlangan. "
        "Chegirma stavkasi (discount rate) yiliga 13.5% darajasida qabul qilingan."
    )

    for tbl in tables:
        doc.add_heading(f"{tbl.get('ilova', '')}: {tbl.get('title', '')}", level=2)
        headers = tbl.get("headers", [])
        rows = tbl.get("rows", [])

        t = doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        _set_table_borders(t)

        for idx, h in enumerate(headers):
            c = t.rows[0].cells[idx]
            c.text = str(h)
            _set_cell_background(c, LIGHT_BG_HEX)
            c.paragraphs[0].runs[0].bold = True
            c.paragraphs[0].runs[0].font.size = Pt(8.5)

        for r in rows:
            rc = t.add_row().cells
            first_col_val = str(r[0] if r else "").upper()
            is_tot = any(w in first_col_val for w in ["JAMI", "UMUMIY", "SOF FOYDA", "SOF PUL OQIMI", "YALPI JAMI", "SOF JORIY"])
            for idx, cell_val in enumerate(r):
                if idx < len(rc):
                    _set_cell_margins(rc[idx], top=60, bottom=60, left=80, right=80)
                    if isinstance(cell_val, float):
                        rc[idx].text = f"{cell_val:,.0f}"
                    else:
                        rc[idx].text = str(cell_val if cell_val is not None else "")
                    if is_tot:
                        _set_cell_background(rc[idx], TOTAL_BG_HEX)
                        if rc[idx].paragraphs[0].runs:
                            rc[idx].paragraphs[0].runs[0].bold = True
                    if rc[idx].paragraphs[0].runs:
                        rc[idx].paragraphs[0].runs[0].font.size = Pt(8.0)

        doc.add_paragraph()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path

import os
import math
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


FAOLIYAT_NOMLARI = {
    "ishlab_chiqarish": "Ishlab chiqarish",
    "qishloq_xojaligi": "Qishloq xo'jaligi",
    "savdo": "Savdo bizneslari",
    "xizmat": "Xizmat ko'rsatish",
}

# ── 10-YILLIK LOYIHA GORIZONTI ──
N_YEARS = 10
DISCOUNT_RATE_PCT = 13.5  # O'zbekiston banklari uchun standart chegirma stavkasi
DISCOUNT_RATES = [round(1.0 / ((1 + DISCOUNT_RATE_PCT / 100) ** (y + 1)), 6) for y in range(N_YEARS)]
# Ishlab chiqarish quvvatining yillar bo'yicha o'sishi: 50% → 100%
CAPACITY_RATES = [0.50, 0.55, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]


def _num(val, default=0.0) -> float:
    if val is None or val == "":
        return float(default)
    if isinstance(val, (int, float)):
        return float(val)
    try:
        cleaned = str(val).replace(" ", "").replace("\u00a0", "").replace("\u202f", "").replace(",", ".")
        return float(cleaned)
    except Exception:
        return float(default)


def _int(val, default=0) -> int:
    return int(round(_num(val, default)))


def _calculate_irr(investment: float, cash_flows: list[float]) -> float:
    if investment <= 0 or not cash_flows or sum(cash_flows) <= investment:
        return 0.0
    low, high = -0.5, 5.0
    for _ in range(80):
        mid = (low + high) / 2.0
        if mid <= -0.99:
            mid = -0.99
        npv = -investment + sum(cf / ((1.0 + mid) ** (i + 1)) for i, cf in enumerate(cash_flows))
        if abs(npv) < 1.0:
            return round(mid * 100.0, 2)
        if npv > 0:
            low = mid
        else:
            high = mid
    return round(((low + high) / 2.0) * 100.0, 2)


def calculate_financial_model(payload: dict) -> dict:
    faoliyat_turi = (payload.get("faoliyat_turi") or "ishlab_chiqarish").strip()
    faoliyat_nomi = FAOLIYAT_NOMLARI.get(faoliyat_turi, "Ishlab chiqarish")

    loyiha_nomi = (payload.get("loyiha_nomi") or "").strip()
    tashabbuskor = (payload.get("tashabbuskor") or "").strip()
    fio = (payload.get("fio") or "").strip()
    mulk = (payload.get("mulk") or "").strip()
    stir = (payload.get("stir") or "").strip()
    manzil = (payload.get("manzil") or "").strip()
    bank = (payload.get("bank") or "").strip()
    soliq_turi = (payload.get("soliq_turi") or "ytt").strip()
    mahsulot = (payload.get("mahsulot") or loyiha_nomi or "").strip()
    olchov = (payload.get("olchov") or "dona").strip()

    loyiha_qiymati = _num(payload.get("loyiha_qiymati"), 0.0)
    oz_mablag = _num(payload.get("oz_mablag"), 0.0)
    kredit = _num(payload.get("kredit"), 0.0)
    if loyiha_qiymati <= 0 and (oz_mablag + kredit) > 0:
        loyiha_qiymati = oz_mablag + kredit

    foiz = _num(payload.get("foiz"), 14.0)
    muddat = _int(payload.get("muddat"), 36)
    if muddat <= 0:
        muddat = 36
    imtiyoz = _int(payload.get("imtiyoz"), 0)
    if imtiyoz >= muddat:
        imtiyoz = max(0, muddat - 1)
    kredit_turi = (payload.get("kredit_turi") or "annuitet").strip()

    hajm = _num(payload.get("hajm"), 0.0)
    narx = _num(payload.get("narx"), 0.0)
    max_revenue = hajm * narx

    # Dynamic cost fields
    xomashyo_birlik = _num(payload.get("xomashyo_narx") or payload.get("tovar_xaridi"), 0.0)
    urug_yem_yillik = _num(payload.get("urug_yem_narx"), 0.0)
    texnika_xarajat = _num(payload.get("texnika_xarajat"), 0.0)
    yer_ijarasi = _num(payload.get("yer_ijarasi"), 0.0)
    oylik_ijara = _num(payload.get("dokon_ijarasi") or payload.get("joy_ijarasi"), 0.0)
    transport_oylik = _num(payload.get("transport_xarajat"), 0.0)

    # Staff
    direktor = _int(payload.get("direktor"), 1)
    rahbar_oylik = _num(payload.get("rahbar_oylik"), 0.0)
    xodim = _int(payload.get("xodim"), 0)
    ishchi_oylik = _num(payload.get("ishchi_oylik"), 0.0)
    yangi_xodim = _int(payload.get("yangi_xodim"), 0)
    yangi_ishchi_oylik = _num(payload.get("yangi_ishchi_oylik"), 0.0)

    # Utilities
    elektr = _num(payload.get("elektr"), 0.0)
    gaz = _num(payload.get("gaz"), 0.0)
    suv = _num(payload.get("suv"), 0.0)
    oqava = _num(payload.get("oqava"), 0.0)

    # 1-3 ILOVA: Loyiha qiymati va moliyalashtirish
    asosiy_oz = round(oz_mablag * 0.85, 2)
    aylanma_oz = round(oz_mablag - asosiy_oz, 2)
    asosiy_kredit = round(kredit, 2)
    jami_asosiy = round(asosiy_oz + asosiy_kredit, 2)
    total_funding = oz_mablag + kredit if (oz_mablag + kredit) > 0 else loyiha_qiymati
    oz_ulush = f"{(oz_mablag / total_funding * 100):.1f}%" if total_funding > 0 else "0.0%"
    kr_ulush = f"{(kredit / total_funding * 100):.1f}%" if total_funding > 0 else "0.0%"

    # 4-ILOVA: Amortizatsiya (15% stavka, 10 yillik)
    amort_yearly = round(jami_asosiy * 0.15, 2)
    amort_rows_years = [amort_yearly if (i + 1) * amort_yearly <= jami_asosiy else max(0.0, round(jami_asosiy - i * amort_yearly, 2)) for i in range(N_YEARS)]
    cum_amort = []
    s_a = 0.0
    for a in amort_rows_years:
        s_a = round(s_a + a, 2)
        cum_amort.append(s_a)

    # 5-ILOVA: Ish haqi
    rahbar_oylik_jami = round(direktor * rahbar_oylik, 2)
    rahbar_yillik_jami = round(rahbar_oylik_jami * 12, 2)
    rahbar_ijtimoiy = round(rahbar_yillik_jami * 0.12, 2)
    rahbar_total = round(rahbar_yillik_jami + rahbar_ijtimoiy, 2)

    ishchi_oylik_jami = round(xodim * ishchi_oylik, 2)
    ishchi_yillik_jami = round(ishchi_oylik_jami * 12, 2)
    xizmat_oylik_jami = round(yangi_xodim * yangi_ishchi_oylik, 2)
    xizmat_yillik_jami = round(xizmat_oylik_jami * 12, 2)

    prod_staff_count = xodim + yangi_xodim
    prod_oylik_jami = round(ishchi_oylik_jami + xizmat_oylik_jami, 2)
    prod_yillik_jami = round(ishchi_yillik_jami + xizmat_yillik_jami, 2)
    prod_ijtimoiy = round(prod_yillik_jami * 0.12, 2)
    prod_total = round(prod_yillik_jami + prod_ijtimoiy, 2)

    all_staff_count = direktor + prod_staff_count
    all_oylik_jami = round(rahbar_oylik_jami + prod_oylik_jami, 2)
    all_yillik_jami = round(rahbar_yillik_jami + prod_yillik_jami, 2)
    all_ijtimoiy = round(rahbar_ijtimoiy + prod_ijtimoiy, 2)
    yalpi_ish_haqi = round(all_yillik_jami + all_ijtimoiy, 2)

    # KOMMUNAL
    el_oy = round(elektr * 900, 2)
    gaz_oy = round(gaz * 1500, 2)
    suv_oy = round(suv * 3000, 2)
    oq_oy = round(oqava * 2000, 2)
    kom_oy_jami = round(el_oy + gaz_oy + suv_oy + oq_oy, 2)
    kom_yil_jami = round(kom_oy_jami * 12, 2)

    # 8-9 ILOVA: Kredit to'lov jadvali (10 yilga bo'lingan)
    r_month = (foiz / 100.0) / 12.0
    asosiy_muddat = max(1, muddat - imtiyoz)
    qoldiq = kredit
    yearly_principal = [0.0] * N_YEARS
    yearly_interest = [0.0] * N_YEARS
    yearly_total_pay = [0.0] * N_YEARS
    yearly_end_balance = [0.0] * N_YEARS

    if kredit > 0:
        for m in range(1, muddat + 1):
            y_idx = min(N_YEARS - 1, (m - 1) // 12)
            f_tolov = qoldiq * r_month
            if m <= imtiyoz:
                a_tolov = 0.0
                tolov = f_tolov
            else:
                if kredit_turi == "annuitet" and r_month > 0:
                    tolov = kredit * (r_month * math.pow(1 + r_month, asosiy_muddat)) / (math.pow(1 + r_month, asosiy_muddat) - 1)
                    a_tolov = tolov - f_tolov
                else:
                    a_tolov = kredit / asosiy_muddat
                    tolov = a_tolov + f_tolov
                qoldiq = max(0.0, qoldiq - a_tolov)
            yearly_principal[y_idx] = round(yearly_principal[y_idx] + a_tolov, 2)
            yearly_interest[y_idx] = round(yearly_interest[y_idx] + f_tolov, 2)
            yearly_total_pay[y_idx] = round(yearly_total_pay[y_idx] + tolov, 2)
            yearly_end_balance[y_idx] = round(qoldiq, 2)

    # 6-ILOVA: 10 yillik sotish rejasi
    revenues = [round(max_revenue * cap, 2) for cap in CAPACITY_RATES]
    volumes = [round(hajm * cap, 2) for cap in CAPACITY_RATES]

    # Xomashyo bazaviy yillik xarajat (100% quvvatda)
    if xomashyo_birlik > 0 and hajm > 0:
        base_raw_material = xomashyo_birlik * hajm
    elif urug_yem_yillik > 0:
        base_raw_material = urug_yem_yillik + texnika_xarajat
    elif max_revenue > 0:
        ratio = 0.45 if faoliyat_turi == "ishlab_chiqarish" else (0.60 if faoliyat_turi == "savdo" else (0.35 if faoliyat_turi == "qishloq_xojaligi" else 0.25))
        base_raw_material = max_revenue * ratio
    else:
        base_raw_material = 0.0

    raw_materials_yearly = [round(base_raw_material * cap, 2) for cap in CAPACITY_RATES]
    prod_wages_yearly = [round(prod_total * cap, 2) for cap in CAPACITY_RATES]
    kommunal_yearly = [round(kom_yil_jami * (0.8 + 0.2 * cap), 2) for cap in CAPACITY_RATES]
    tannarx_yearly = [round(raw_materials_yearly[i] + prod_wages_yearly[i] + amort_rows_years[i] + kommunal_yearly[i], 2) for i in range(N_YEARS)]

    # Davr xarajatlari
    admin_yearly = [round(rahbar_total + (oylik_ijara * 12) + yer_ijarasi + (revenues[i] * 0.02), 2) for i in range(N_YEARS)]
    marketing_yearly = [round(revenues[i] * 0.015 + (transport_oylik * 12), 2) for i in range(N_YEARS)]
    service_yearly = [round(jami_asosiy * 0.01 + revenues[i] * 0.01, 2) for i in range(N_YEARS)]
    other_yearly = [round(revenues[i] * 0.01, 2) for i in range(N_YEARS)]
    davr_yearly = [round(admin_yearly[i] + marketing_yearly[i] + service_yearly[i] + other_yearly[i], 2) for i in range(N_YEARS)]
    op_expenses_yearly = [round(tannarx_yearly[i] + davr_yearly[i], 2) for i in range(N_YEARS)]
    full_cost_yearly = [round(op_expenses_yearly[i] + yearly_interest[i], 2) for i in range(N_YEARS)]

    # 7-ILOVA: Soliqlar
    tax_rate = 0.04 if soliq_turi == "ytt" else 0.12
    tax_label = "Yagona soliq (YTT)" if soliq_turi == "ytt" else "QQS va Foyda solig'i (MCHJ)"
    tax_rate_str = "4%" if soliq_turi == "ytt" else "12%"
    main_tax_yearly = [round(revenues[i] * tax_rate, 2) for i in range(N_YEARS)]
    social_tax_yearly = [round(all_ijtimoiy * CAPACITY_RATES[i], 2) for i in range(N_YEARS)]
    total_tax_yearly = [round(main_tax_yearly[i] + social_tax_yearly[i], 2) for i in range(N_YEARS)]

    # 12-ILOVA: Foyda va zararlar
    gross_profit_yearly = [round(revenues[i] - tannarx_yearly[i], 2) for i in range(N_YEARS)]
    op_profit_yearly = [round(gross_profit_yearly[i] - davr_yearly[i], 2) for i in range(N_YEARS)]
    ebt_yearly = [round(op_profit_yearly[i] - yearly_interest[i], 2) for i in range(N_YEARS)]
    net_profit_yearly = [round(ebt_yearly[i] - total_tax_yearly[i], 2) for i in range(N_YEARS)]
    net_margin_yearly = [f"{(net_profit_yearly[i] / revenues[i] * 100):.1f}%" if revenues[i] > 0 else "0.0%" for i in range(N_YEARS)]

    # 13-ILOVA: Pul oqimi (Cash Flow)
    op_cash_flow = [round(gross_profit_yearly[i] + amort_rows_years[i] - davr_yearly[i], 2) for i in range(N_YEARS)]
    net_cash_flow = [round(op_cash_flow[i] - yearly_interest[i] - total_tax_yearly[i] - yearly_principal[i], 2) for i in range(N_YEARS)]
    cum_cash_flow = []
    c_cf = -loyiha_qiymati
    for cf in net_cash_flow:
        c_cf = round(c_cf + cf, 2)
        cum_cash_flow.append(c_cf)

    # 14-ILOVA: NPV, IRR, ROI, Payback
    pv_flows = [round(net_cash_flow[i] * DISCOUNT_RATES[i], 2) for i in range(N_YEARS)]
    total_pv = round(sum(pv_flows), 2)
    npv = round(total_pv - loyiha_qiymati, 2)
    pi = round(total_pv / loyiha_qiymati, 4) if loyiha_qiymati > 0 else 0.0
    avg_net_profit = sum(net_profit_yearly) / float(N_YEARS)
    roi = round((avg_net_profit / loyiha_qiymati) * 100.0, 2) if loyiha_qiymati > 0 else 0.0
    irr = _calculate_irr(loyiha_qiymati, net_cash_flow)
    payback = round(loyiha_qiymati / avg_net_profit, 2) if avg_net_profit > 0 and loyiha_qiymati > 0 else 0.0

    warning = ""
    if npv <= 0:
        warning = (
            "DIQQAT: Loyiha o'zini oqlamaydi (NPV salbiy). "
            "Rentabellikni oshirish uchun mahsulot/xizmat narxini ko'taring yoki xarajatlarni qisqartiring."
        )

    # 10-ILOVA: Zararsizlanish nuqtasi
    y1_fixed = round(amort_rows_years[0] + admin_yearly[0] + yearly_interest[0], 2)
    y1_var = round(raw_materials_yearly[0] + prod_wages_yearly[0] + kommunal_yearly[0] + marketing_yearly[0] + service_yearly[0] + other_yearly[0], 2)
    y1_total_cost = round(y1_fixed + y1_var, 2)
    bep = round(y1_fixed / (1.0 - (y1_var / revenues[0])), 2) if revenues[0] > y1_var and revenues[0] > 0 else 0

    tables = [
        {
            "ilova": "1-ILOVA",
            "title": "LOYIHA QIYMATI",
            "headers": ["Ko'rsatkich", "O'z mablag' (so'm)", "Bank krediti (so'm)", "Jami (so'm)"],
            "rows": [
                ["Asosiy vositalarni sotib olish (jihozlar)", 0, asosiy_kredit, asosiy_kredit],
                ["Asosiy vositalar (o'z mablag')", asosiy_oz, 0, asosiy_oz],
                ["JAMI asosiy mablag'lar", asosiy_oz, asosiy_kredit, jami_asosiy],
                ["Aylanma kapital", aylanma_oz, 0, aylanma_oz],
                ["LOYIHA QIYMATI", oz_mablag, kredit, loyiha_qiymati],
            ],
        },
        {
            "ilova": "2-ILOVA",
            "title": "Moliyalashtirish rejasi",
            "headers": ["Manba", "Summa (so'm)", "Ulush"],
            "rows": [
                ["O'z mablag'lari", oz_mablag, oz_ulush],
                ["Bank krediti", kredit, kr_ulush],
                ["JAMI moliyalashtirish", loyiha_qiymati, "100%"],
            ],
        },
        {
            "ilova": "3-ILOVA",
            "title": "Loyiha ishtirokchilari hissasi",
            "headers": ["Ko'rsatkich", "O'z mablag' (so'm)", "Kredit (so'm)", "Jami (so'm)"],
            "rows": [
                ["Asosiy vositalar (o'z mablag')", asosiy_oz, 0, asosiy_oz],
                ["Asosiy vositalar (kredit)", 0, asosiy_kredit, asosiy_kredit],
                ["Sug'urta xarajatlari", 0, 0, 0],
                ["Boshqa xarajatlar", 0, 0, 0],
                ["Aylanma kapital", aylanma_oz, 0, aylanma_oz],
                ["JAMI ASOSIY KAPITAL", oz_mablag, kredit, loyiha_qiymati],
            ],
        },
        {
            "ilova": "4-ILOVA",
            "title": "AMORTIZATSIYA HISOB-KITOBI",
            "headers": ["Ko'rsatkich", "Qiymat (so'm)", "Stavka", *[f"{i+1}-yil" for i in range(N_YEARS)]],
            "rows": [
                ["Asosiy vositalar", jami_asosiy, "15%", *amort_rows_years],
                ["Jami amortizatsiya", "", "", *amort_rows_years],
                ["Yig'ilgan amortizatsiya", "", "", *cum_amort],
            ],
        },
        {
            "ilova": "5-ILOVA",
            "title": "ISH HAQI XARAJATLARI",
            "headers": ["Lavozim", "Soni", "Oylik maosh", "Oylik jami", "Yillik jami"],
            "rows": [
                ["Rahbariyat", "", "", "", ""],
                ["Direktor", direktor, rahbar_oylik, rahbar_oylik_jami, rahbar_yillik_jami],
                ["Jami rahbariyat", direktor, "", rahbar_oylik_jami, rahbar_yillik_jami],
                ["Ijtimoiy soliq (12%)", "", "12%", "", rahbar_ijtimoiy],
                ["JAMI rahbariyat", "", "", "", rahbar_total],
                ["", "", "", "", ""],
                ["Ishlab chiqarish xodimlari", "", "", "", ""],
                ["Ishchilar", xodim, ishchi_oylik, ishchi_oylik_jami, ishchi_yillik_jami],
                ["Xizmat ko'rsatuvchilar", yangi_xodim, yangi_ishchi_oylik, xizmat_oylik_jami, xizmat_yillik_jami],
                ["Jami ishlab chiqarish", prod_staff_count, "", prod_oylik_jami, prod_yillik_jami],
                ["Ijtimoiy soliq (12%)", "", "12%", "", prod_ijtimoiy],
                ["JAMI ishlab chiqarish", "", "", "", prod_total],
                ["", "", "", "", ""],
                ["JAMI ISH HAQI FONDI", all_staff_count, "", all_oylik_jami, all_yillik_jami],
                ["Ijtimoiy soliq (12%)", "", "12%", "", all_ijtimoiy],
                ["YALPI JAMI", "", "", "", yalpi_ish_haqi],
            ],
        },
        {
            "ilova": "KOMMUNAL",
            "title": "KOMMUNIKATSIYA VA INFRATUZILMA XARAJATLARI",
            "headers": ["Xarajat turi", "O'lchov birligi", "Miqdori (oylik)", "Tarif (so'm)", "Oylik xarajat (so'm)", "Yillik xarajat (so'm)"],
            "rows": [
                ["Elektr energiyasi", "kVT", elektr, 900, el_oy, round(el_oy * 12, 2)],
                ["Tabiiy gaz", "m3", gaz, 1500, gaz_oy, round(gaz_oy * 12, 2)],
                ["Ichimlik suvi", "m3", suv, 3000, suv_oy, round(suv_oy * 12, 2)],
                ["Oqava suv (Kanalizatsiya)", "m3", oqava, 2000, oq_oy, round(oq_oy * 12, 2)],
                ["JAMI", "", "", "", kom_oy_jami, kom_yil_jami],
            ],
        },
        {
            "ilova": "6-ILOVA",
            "title": "XIZMAT KO'RSATISH VA SOTISH REJASI",
            "headers": ["Ishlab chiqariladigan mahsulot nomi", "Yillik ishlab chiqarish hajmi", "O'lchov birligi", "Bitta mahsulotning sotish narxi", "1 yillik savdo tushumi"],
            "rows": [[mahsulot, hajm, olchov, narx, max_revenue]],
        },
        {
            "ilova": "6-ILOVA",
            "title": "XIZMAT KO'RSATISH VA SOTISH REJASI",
            "headers": ["Mahsulot nomi (xizmat turi)", "Ishlab chiqarish hajmi", "Sotish narxi", "Tushgan daromad (jami)"],
            "rows": [
                ["MAKSIMAL QUVVAT (100%)", hajm, narx, max_revenue],
                *[[f"{i+1}-yil reja ({int(CAPACITY_RATES[i]*100)}%)", volumes[i], narx, revenues[i]] for i in range(N_YEARS)],
            ],
        },
        {
            "ilova": "8-9-ILOVA",
            "title": "KREDIT TO'LOV JADVALI (Oyma-oy)",
            "headers": ["Davr", "Asosiy qarz (so'm)", "Foiz to'lov (so'm)", "Jami to'lov (so'm)", "Qoldiq (so'm)"],
            "rows": [
                ["", "", "", "", ""],
                ["YILLIK TO'LOVLAR", "", "", "", ""],
                *[[f"{i+1}-yil jami", yearly_principal[i], yearly_interest[i], yearly_total_pay[i], yearly_end_balance[i]] for i in range(N_YEARS)],
                ["UMUMIY JAMI", round(sum(yearly_principal), 2), round(sum(yearly_interest), 2), round(sum(yearly_total_pay), 2), 0],
            ],
        },
        {
            "ilova": "7-ILOVA",
            "title": "SOLIQ VA BOJLAR",
            "headers": ["Ko'rsatkich", "Stavka", *[f"{i+1}-yil" for i in range(N_YEARS)]],
            "rows": [
                [tax_label, tax_rate_str, *main_tax_yearly],
                ["Ijtimoiy soliq (12%)", "12%", *social_tax_yearly],
                ["JAMI SOLIQLAR", "", *total_tax_yearly],
            ],
        },
        {
            "ilova": "10-ILOVA",
            "title": "TO'LIQ QUVVATLI BO'LGAN ISHLAB CHIQARISH XARAJATLARI (1-yil uchun)",
            "headers": ["XARAJATLAR", "TO'LIQ XARAJATLAR (so'm)", "DOIMIY xarajat", "Ulush", "O'ZGARUVCHAN xarajat", "Ulush"],
            "rows": [
                ["TO'G'RIDAN TO'G'RI XARAJATLAR", y1_total_cost, y1_fixed, "", y1_var, ""],
                ["", "", "", "", "", ""],
                ["", "", "", "", "", ""],
                ["JAMI XARAJATLAR", y1_total_cost, y1_fixed, "", y1_var, ""],
                ["TO'LIQ QUVVATDA SOTISH", revenues[0], "", "", "", ""],
                ["ZARARSIZLANISH NUQTASI (so'm)", bep, "", "", "", ""],
            ],
        },
        {
            "ilova": "11-ILOVA",
            "title": "TO'LIQ YILLIK XARAJATLAR (TANNARX)",
            "headers": ["Xarajat moddalari", "Birlik", *[f"{i+1}-yil" for i in range(N_YEARS)]],
            "rows": [
                ["Rivojlanish quvvati", "%", *[f"{int(cap*100)}%" for cap in CAPACITY_RATES]],
                ["Xomashyo va materiallar", "so'm", *raw_materials_yearly],
                ["Ishlab chiqarish ish haqi", "so'm", *prod_wages_yearly],
                ["Amortizatsiya", "so'm", *amort_rows_years],
                ["Kommunal xarajatlar", "so'm", *kommunal_yearly],
                ["TANNARX", "so'm", *tannarx_yearly],
                ["", "", *["" for _ in range(N_YEARS)]],
                ["Ma'muriyat xarajatlari", "so'm", *admin_yearly],
                ["Marketing xarajatlar", "so'm", *marketing_yearly],
                ["Texnik xizmat", "so'm", *service_yearly],
                ["Boshqa xarajatlar", "so'm", *other_yearly],
                ["Davr xarajatlari", "so'm", *davr_yearly],
                ["Operatsion xarajatlar", "so'm", *op_expenses_yearly],
                ["Kredit foizlari", "so'm", *yearly_interest],
                ["SOTILGAN MAHSULOTLARNING XARAJATLARI (TANNARX)", "so'm", *full_cost_yearly],
            ],
        },
        {
            "ilova": "12-ILOVA",
            "title": "KUTILAYOTGAN FOYDA VA ZARARLAR TO'G'RISIDA HISOBOT",
            "headers": ["Ko'rsatgichlar", "Birlik", *[f"{i+1}-yil" for i in range(N_YEARS)]],
            "rows": [
                ["Sotishdan tushgan daromad", "so'm", *revenues],
                ["Sof sotishdan tushgan daromad", "so'm", *revenues],
                ["Tannarx (xizmatlar)", "so'm", *tannarx_yearly],
                ["Umumiy daromad (yalpi foyda)", "so'm", *gross_profit_yearly],
                ["Ma'muriy xarajatlar", "so'm", *admin_yearly],
                ["Marketing xarajatlar", "so'm", *marketing_yearly],
                ["Boshqa xarajatlar", "so'm", *other_yearly],
                ["Operatsion foyda", "so'm", *op_profit_yearly],
                ["Kredit foizlari", "so'm", *yearly_interest],
                ["Soliq to'laguncha foyda", "so'm", *ebt_yearly],
                ["Soliqlar", "so'm", *total_tax_yearly],
                ["SOF FOYDA (ZARAR)", "so'm", *net_profit_yearly],
                ["Sof rentabellik", "%", *net_margin_yearly],
            ],
        },
        {
            "ilova": "13-ILOVA",
            "title": "PUL OQIMI (CASH FLOW)",
            "headers": ["Ko'rsatgichlar", *[f"{i+1}-yil" for i in range(N_YEARS)]],
            "rows": [
                ["Investitsiyalar", -loyiha_qiymati, *["" for _ in range(N_YEARS - 1)]],
                ["Sotishdan tushgan tushum", *revenues],
                ["Sotishdan tushgan naqd pul", *revenues],
                ["Xizmat xarajatlari (tannarx)", *tannarx_yearly],
                ["Yalpi pul tushumi", *gross_profit_yearly],
                ["Amortizatsiya (+)", *amort_rows_years],
                ["Marketing xarajatlar", *marketing_yearly],
                ["Ma'muriy xarajatlar", *admin_yearly],
                ["Boshqa xarajatlar", *other_yearly],
                ["Operatsion pul oqimi", *op_cash_flow],
                ["Foiz to'lovlari", *yearly_interest],
                ["Soliqlar", *total_tax_yearly],
                ["Asosiy qarz qaytarish", *yearly_principal],
                ["SOF PUL OQIMI", *net_cash_flow],
                ["KUMULYATIV PUL OQIMI", *cum_cash_flow],
            ],
        },
        {
            "ilova": "14-ILOVA",
            "title": "LOYIHANING IQTISODIY SAMARADORLIK KO'RSATKICHLARI",
            "headers": ["Ko'rsatkich", "Sof pul oqimi", f"{DISCOUNT_RATE_PCT}% chegirma koeffitsienti", "Joriy qiymat"],
            "rows": [
                ["Investitsion xarajatlar", -loyiha_qiymati, "", ""],
                *[[f"{i+1}-yil", net_cash_flow[i], f"{DISCOUNT_RATES[i]:.6f}", pv_flows[i]] for i in range(N_YEARS)],
                ["", "", "", ""],
                ["Jami joriy qiymat (JJQ)", "", "", total_pv],
                ["Investitsion xarajatlar (IX)", "", "", -loyiha_qiymati],
                ["SOF JORIY QIYMAT (SJQ=JJQ-IX)", "", "", npv],
                ["Rentabellik indeksi (IR)", "", "", f"{pi:.4f}"],
                ["Ichki daromad darajasi (IRR)", "", "", f"{irr:.1f}%" if irr > 0 else "—"],
                ["Investitsiyalarni qaytarish muddati", "", "", f"{payback:.1f} yil"],
            ],
        },
    ]

    context = {
        "bank": bank,
        "berilgan_vaqti": payload.get("ro_sana") or datetime.now().strftime("%d.%m.%Y"),
        "direktor": direktor,
        "discount_rate": 13.5,
        "elektr": elektr,
        "faoliyat": payload.get("faoliyat_turi_text") or "",
        "faoliyat_turi": faoliyat_turi,
        "faoliyat_turi_nomi": faoliyat_nomi,
        "fio": fio,
        "foiz": foiz,
        "gaz": gaz,
        "hajm": hajm,
        "imtiyoz": imtiyoz,
        "irr": irr,
        "ishchi_oylik": ishchi_oylik,
        "jshshir": "",
        "kredit": kredit,
        "kredit_turi": kredit_turi,
        "loyiha_nomi": loyiha_nomi,
        "loyiha_qiymati": loyiha_qiymati,
        "mahsulot": mahsulot,
        "manzil": manzil,
        "muddat": muddat,
        "mulk": mulk,
        "narx": narx,
        "npv": npv,
        "olchov": olchov,
        "oqava": oqava,
        "oz_mablag": oz_mablag,
        "pasport": "",
        "payback": payback,
        "pi": pi,
        "rahbar_oylik": rahbar_oylik,
        "roi": roi,
        "soliq_turi": soliq_turi,
        "stir": stir,
        "suv": suv,
        "tashabbuskor": tashabbuskor,
        "warning": warning,
        "xodim": xodim,
        "yangi_ishchi_oylik": yangi_ishchi_oylik,
        "yangi_xodim": yangi_xodim,
        "yillik_daromad": revenues[0],
        "yillik_sof_foyda": net_profit_yearly[0],
    }

    indicators = {
        "discount_rate": 13.5,
        "irr": irr,
        "jami_daromad": round(sum(revenues), 2),
        "jami_sof_foyda": round(sum(net_profit_yearly), 2),
        "kredit": kredit,
        "loyiha_qiymati": loyiha_qiymati,
        "npv": npv,
        "oz_mablag": oz_mablag,
        "payback": payback,
        "pi": pi,
        "roi": roi,
        "warning": warning,
    }

    return {
        "context": context,
        "faoliyat_nomi": faoliyat_nomi,
        "faoliyat_turi": faoliyat_turi,
        "indicators": indicators,
        "tables": tables,
    }


def generate_docx_report(model_data: dict, output_path: str) -> str:
    ctx = model_data["context"]
    ind = model_data["indicators"]
    tables = model_data["tables"]

    doc = Document()

    # Title section
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run(f"BIZNES-REJA\n«{ctx.get('loyiha_nomi') or 'Investitsiya loyihasi'}»")
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(30, 58, 138)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run(
        f"Tashabbuskor: {ctx.get('tashabbuskor') or 'Korxona'}\n"
        f"Rahbar: {ctx.get('fio') or '—'} | Manzil: {ctx.get('manzil') or 'O`zbekiston'}\n"
        f"Sana: {datetime.now().strftime('%d.%m.%Y')} yil"
    )
    sub_run.font.size = Pt(11)

    doc.add_paragraph()

    # 1. Loyiha pasporti
    doc.add_heading("1. LOYIHA PASPORTI VA REZYUMESI", level=1)
    passport_items = [
        ("Loyiha nomi", ctx.get("loyiha_nomi") or "—"),
        ("Tashabbuskor", ctx.get("tashabbuskor") or "—"),
        ("Mulkchilik shakli", ctx.get("mulk") or "MCHJ"),
        ("STIR (INN)", ctx.get("stir") or "—"),
        ("Rahbar F.I.O.", ctx.get("fio") or "—"),
        ("Xizmat ko'rsatuvchi bank", ctx.get("bank") or "Tijorat banki"),
        ("Faoliyat yo'nalishi", ctx.get("faoliyat_turi_nomi") or "—"),
        ("Loyiha umumiy qiymati", f"{ctx.get('loyiha_qiymati', 0):,.0f} so'm"),
        ("O'z mablag'lari", f"{ctx.get('oz_mablag', 0):,.0f} so'm"),
        ("Bank krediti", f"{ctx.get('kredit', 0):,.0f} so'm ({ctx.get('foiz')}% yillik, {ctx.get('muddat')} oy)"),
        ("Sof joriy qiymat (NPV)", f"{ind.get('npv', 0):,.0f} so'm"),
        ("Ichki daromadlilik normasi (IRR)", f"{ind.get('irr', 0):.1f}%"),
        ("Investitsiya rentabelligi (ROI)", f"{ind.get('roi', 0):.1f}%"),
        ("O'zini qoplash muddati (Payback)", f"{ind.get('payback', 0):.1f} yil"),
    ]

    p_table = doc.add_table(rows=1, cols=2)
    p_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    p_table.style = "Table Grid"
    hdr = p_table.rows[0].cells
    hdr[0].text = "Ko'rsatkich"
    hdr[1].text = "Qiymati"
    for k, v in passport_items:
        row_cells = p_table.add_row().cells
        row_cells[0].text = str(k)
        row_cells[1].text = str(v)

    doc.add_paragraph()

    # 2. Marketing va SWOT tahlil
    doc.add_heading("2. BOZOR, MARKETING VA SWOT TAHLIL", level=1)
    doc.add_paragraph(
        f"Ushbu biznes-reja «{ctx.get('tashabbuskor') or 'Tashabbuskor'}» tomonidan "
        f"«{ctx.get('loyiha_nomi') or 'Biznes loyiha'}» yo'nalishida zamonaviy va raqobatbardosh faoliyatni "
        f"yo'lga qo'yish, yangi ish o'rinlari yaratish hamda bank kreditini o'z vaqtida qaytarish maqsadida ishlab chiqilgan."
    )

    # 3. Barcha moliyaviy jadvallar
    doc.add_heading("3. MOLIYAVIY HISOB-KITOBLAR VA ILOVALAR", level=1)
    for tbl in tables:
        doc.add_heading(f"{tbl['ilova']}: {tbl['title']}", level=2)
        headers = tbl["headers"]
        rows = tbl["rows"]
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        for idx, h in enumerate(headers):
            t.rows[0].cells[idx].text = str(h)
        for r in rows:
            rc = t.add_row().cells
            for idx, cell_val in enumerate(r):
                if idx < len(rc):
                    if isinstance(cell_val, float):
                        rc[idx].text = f"{cell_val:,.0f}"
                    else:
                        rc[idx].text = str(cell_val)
        doc.add_paragraph()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path

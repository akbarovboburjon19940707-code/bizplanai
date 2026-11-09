"""10 yillik moliyaviy model: "Asosiy shablon npv 10 yillik.xls" mantiqi asosida.

Excel shablonining formulalari aynan takrorlanadi (docs/EXCEL_SHABLON_TAHLILI.md), quyidagi tuzatishlar bilan
(foydalanuvchi qarori, 2026-11-10):
- aylanma kapital va moliyaviy xarajatlar loyiha qiymatiga bir marta qo'shiladi (Excel'da ikki marta);
- asosiy qarz to'lovi har yil kredit jadvalidan olinadi (Excel'da 6-10 yillarda 25 mln qo'lda yozilgan);
- qoplash muddati (PP) va diskontlangan qoplash muddati (DPP) hisoblanadi (Excel'da "3 yil" matni);
- PI = diskontlangan oqimlar yig'indisi / investitsiya (Excel'da NPV / investitsiya);
- ijtimoiy soliq faqat ish haqi xarajatida (eski yadroda soliqlarda ikkinchi marta qo'shilardi).
- tovar/xomashyo xarajati: 1 birlik narxi kiritilsa shu bo'yicha, aks holda `tannarx_ulushi` yoki faoliyat turiga
  qarab standart ulush (DEFAULT_COGS_SHARE); har doim sotuv hajmiga to'liq proporsional (Excel'da 1%, 80% doimiy);
- ijara, transport, urug'/yem/texnika alohida qator (shablonda yo'q, formadagi maydonlar).
Foydalanuvchi qarorlari: NPV/IRR/PP/DPP sof pul oqimidan (soliq va kredit foizidan keyin; Excel'da oldin), 10 yil; soliq YTT 4% / MCHJ 12%;
6 tagacha mahsulot; quvvat grafigi va diskont standart, lekin o'zgartirsa bo'ladi; kredit olish xarajati 2%.
"""
from __future__ import annotations


N_YEARS = 10
DEFAULT_CAPACITY = [0.75, 0.77, 0.80, 0.82, 0.85, 0.90, 0.92, 0.95, 1.00, 1.00]
DEFAULT_DISCOUNT_PCT = 14.0
SOCIAL_TAX = 0.12
LOAN_FEE_RATE = 0.02  # "Kredit olish uchun boshqa xarajatlar" = (kredit + kredit) * 1%
TAX_RATES = {"ytt": (0.04, "Yagona soliq to'lovi (YTT)", "4%"), "mchj": (0.12, "Yagona soliq to'lovi", "12%")}
TARIFFS = {"elektr": ("Elektr energiyasi", "kVt", 900), "gaz": ("Tabiiy gaz", "m3", 1500),
           "suv": ("Ichimlik suvi", "m3", 3000), "oqava": ("Oqava suv (kanalizatsiya)", "m3", 2000)}

# Tovar/xomashyo narxi kiritilmaganda tannarx ulushi (sotish tushumidan), faoliyat turi bo'yicha.
# Shablondagi 1% savdo va ishlab chiqarish uchun real emas (foyda haddan tashqari oshadi), shuning uchun
# o'rtacha ustama/xomashyo ulushiga yaqin standartlar olingan; `tannarx_ulushi` bilan o'zgartiriladi.
DEFAULT_COGS_SHARE = {"savdo": 0.75, "ishlab_chiqarish": 0.55, "qishloq_xojaligi": 0.40, "xizmat": 0.15}
COGS_LABEL = {"savdo": "Sotiladigan tovarlarni xarid qilish", "ishlab_chiqarish": "Xomashyo va materiallar",
              "qishloq_xojaligi": "Xomashyo, materiallar va ishlov berish", "xizmat": "Sarf materiallari"}

# CostTotal varag'i: xarajat moddasi -> doimiy qism ulushi (qolgani quvvatga proporsional)
FIXED_SHARE = {
    "bevosita": 0.0,         # tovar/xomashyo: sotuv hajmiga to'liq proporsional
    "agro": 0.0,             # urug', yem, o'g'it, texnika
    "operatsion": 0.7,       # kommunal
    "amort": 1.0,
    "ishchi": 0.0, "ishchi_ijt": 0.0,
    "admin": 1.0, "admin_ijt": 1.0,
    "boshqa_admin": 0.5, "texnik": 0.7, "marketing": 0.7, "kutilmagan": 0.5,
    "ijara": 1.0, "transport": 0.7,
}


def _r(x: float) -> float:
    return round(float(x), 2)


def _num(val, default=0.0) -> float:
    if val is None or val == "":
        return float(default)
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).replace(" ", "").replace(" ", "").replace(",", "."))
    except ValueError:
        return float(default)


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def irr(flows: list[float]) -> float | None:
    """Ichki daromadlilik darajasi (ulush). Ishorasi o'zgarmasa None."""
    if not flows or all(f >= 0 for f in flows) or all(f <= 0 for f in flows):
        return None

    def npv_at(rate: float) -> float:
        return sum(f / (1 + rate) ** t for t, f in enumerate(flows))

    lo, hi = -0.99, 1.0
    while npv_at(hi) > 0 and hi < 1e6:
        hi *= 2
    if npv_at(lo) * npv_at(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv_at(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _payback(investment: float, flows: list[float]) -> float | None:
    """Kumulyativ oqim investitsiyani qoplagan yil (kasr bilan). Qoplanmasa None."""
    cum = 0.0
    for i, f in enumerate(flows):
        if f > 0 and cum + f >= investment:
            return i + (investment - cum) / f
        cum += f
    return None


def _products(p: dict) -> list[dict]:
    items = p.get("mahsulotlar") or []
    if not items:
        items = [{"nomi": p.get("mahsulot") or p.get("loyiha_nomi") or "Mahsulot", "hajm": p.get("hajm"),
                  "narx": p.get("narx"), "olchov": p.get("olchov"),
                  "xomashyo_narx": p.get("xomashyo_narx") or p.get("tovar_xaridi")}]
    out = []
    for it in items[:6]:
        hajm, narx = _num(it.get("hajm")), _num(it.get("narx"))
        if hajm <= 0 or narx <= 0:
            continue
        out.append({"nomi": (it.get("nomi") or "Mahsulot").strip(), "hajm": hajm, "narx": narx,
                    "olchov": (it.get("olchov") or p.get("olchov") or "dona").strip(),
                    "xomashyo_narx": _num(it.get("xomashyo_narx"))})
    return out


def _loan(kredit: float, foiz_pct: float, muddat: int, imtiyoz: int, turi: str) -> dict:
    r = foiz_pct / 100 / 12
    amort_oy = max(1, muddat - imtiyoz)
    qoldiq = kredit
    asosiy, foiz, tolov, oxir = ([0.0] * N_YEARS for _ in range(4))
    for m in range(1, muddat + 1):
        y = (m - 1) // 12
        f = qoldiq * r
        if m <= imtiyoz:
            a = 0.0
        elif turi == "annuitet" and r > 0:
            a = kredit * r * (1 + r) ** amort_oy / ((1 + r) ** amort_oy - 1) - f
        else:
            a = kredit / amort_oy
        a = min(a, qoldiq)
        qoldiq -= a
        if y < N_YEARS:
            asosiy[y] += a
            foiz[y] += f
            tolov[y] += a + f
            oxir[y] = qoldiq
    return {"asosiy": asosiy, "foiz": foiz, "tolov": tolov, "qoldiq": oxir}


def build_model(p: dict) -> dict:
    # ── 1-3 ILOVA: loyiha qiymati va moliyalashtirish ──
    kredit = _num(p.get("kredit"))
    oz = _num(p.get("oz_mablag"))
    lq_input = _num(p.get("loyiha_qiymati"))
    if oz <= 0 and lq_input > kredit:
        oz = lq_input - kredit
    loyiha_qiymati = oz + kredit if (oz + kredit) > 0 else lq_input
    kredit_xarajat = kredit * LOAN_FEE_RATE
    sugurta = _num(p.get("sugurta"))
    aylanma = _num(p.get("aylanma_kapital"))
    asosiy_oz = oz - aylanma - kredit_xarajat - sugurta
    warnings: list[str] = []
    if asosiy_oz < 0:
        warnings.append("O'z mablag'i aylanma kapital va kredit olish xarajatlarini (kreditning 2%) qoplamaydi.")
        asosiy_oz = 0.0
    asosiy = kredit + asosiy_oz

    # ── 4-ILOVA: amortizatsiya (10 yil, teng) ──
    amort = asosiy / 10

    # ── 5-ILOVA: ish haqi va foydalanish xarajatlari ──
    direktor, rahbar_oylik = int(_num(p.get("direktor"), 1)), _num(p.get("rahbar_oylik"))
    xodim, ishchi_oylik = int(_num(p.get("xodim"))), _num(p.get("ishchi_oylik"))
    yangi, yangi_oylik = int(_num(p.get("yangi_xodim"))), _num(p.get("yangi_ishchi_oylik"))
    admin_wage = direktor * rahbar_oylik * 12
    ishchi_wage = xodim * ishchi_oylik * 12
    yangi_wage = yangi * yangi_oylik * 12
    prod_wage = ishchi_wage + yangi_wage
    admin_ijt, prod_ijt = admin_wage * SOCIAL_TAX, prod_wage * SOCIAL_TAX

    util_rows, kommunal = [], 0.0
    for key, (nomi, birlik, tarif) in TARIFFS.items():
        oylik = _num(p.get(key))
        if oylik > 0:
            yillik = oylik * 12 * tarif
            kommunal += yillik
            util_rows.append([nomi, birlik, _r(oylik * 12), tarif, _r(yillik)])
    boshqa_kom = _num(p.get("boshqa_kommunal"))
    if boshqa_kom > 0:
        kommunal += boshqa_kom
        util_rows.append(["Boshqa kommunal xarajatlar", "so'm", "", "", _r(boshqa_kom)])

    # ── 6-ILOVA: sotish rejasi ──
    products = _products(p)
    cap = [max(0.0, min(_num(c), 150.0)) / 100 for c in (p.get("quvvat") or [])][:N_YEARS]  # foizda
    cap = cap + DEFAULT_CAPACITY[len(cap):]
    max_tushum = sum(pr["hajm"] * pr["narx"] for pr in products)
    tushum = [max_tushum * q for q in cap]

    # ── 10-ILOVA: to'liq quvvatdagi xarajatlar, doimiy / o'zgaruvchan ──
    faoliyat = (p.get("faoliyat_turi") or "ishlab_chiqarish").strip()
    agro = _num(p.get("urug_yem_narx")) + _num(p.get("texnika_xarajat"))
    if p.get("tannarx_ulushi") is not None:
        cogs_share = _num(p.get("tannarx_ulushi")) / 100
    elif agro > 0:  # qishloq xo'jaligida asosiy xarajat urug'/yem qatorida alohida kiritilgan
        cogs_share = 0.0
    else:
        cogs_share = DEFAULT_COGS_SHARE.get(faoliyat, 0.5)
    for pr in products:
        if pr["xomashyo_narx"] > 0:
            pr["tannarx"], pr["tannarx_usul"] = pr["hajm"] * pr["xomashyo_narx"], "1 birlik narxi bo'yicha"
        else:
            pr["tannarx"] = pr["hajm"] * pr["narx"] * cogs_share
            pr["tannarx_usul"] = f"tushumning {cogs_share * 100:g}%"
    bevosita_full = sum(pr["tannarx"] for pr in products)
    full: dict[str, tuple[str, float]] = {}
    if bevosita_full > 0:
        full["bevosita"] = (COGS_LABEL.get(faoliyat, "Xomashyo va materiallar"), bevosita_full)
    if agro > 0:
        full["agro"] = ("Urug', yem, o'g'it va texnika xarajatlari", agro)
    full["operatsion"] = ("Operatsion xarajatlar (kommunal)", kommunal)
    full["amort"] = ("Jami amortizatsiya", amort)
    full["ishchi"] = ("Ishlab chiqarish xodimlarining ish haqi", prod_wage)
    full["ishchi_ijt"] = ("Ijtimoiy soliq (ishchilar)", prod_ijt)
    full["admin"] = ("Ma'muriyat xodimlari ish haqi", admin_wage)
    full["admin_ijt"] = ("Ijtimoiy soliq (ma'muriyat)", admin_ijt)
    full["boshqa_admin"] = ("Boshqa ma'muriy xarajatlar (0,2%)", max_tushum * 0.002)
    full["texnik"] = ("Asosiy vositalarga texnik xizmat va joriy ta'mirlash", amort * 0.01)
    full["marketing"] = ("Marketing xarajatlari (0,2%)", max_tushum * 0.002)
    full["kutilmagan"] = ("Boshqa ko'zda tutilmagan xarajatlar (0,2%)", max_tushum * 0.002)
    ijara = (_num(p.get("dokon_ijarasi")) + _num(p.get("joy_ijarasi"))) * 12 + _num(p.get("yer_ijarasi"))
    if ijara > 0:
        full["ijara"] = ("Ijara xarajatlari", ijara)
    transport = _num(p.get("transport_xarajat")) * 12
    if transport > 0:
        full["transport"] = ("Transport xarajatlari", transport)

    fixed = {k: v * FIXED_SHARE[k] for k, (_, v) in full.items()}
    var = {k: v - fixed[k] for k, (_, v) in full.items()}
    fixed_total, var_total, cost_total = sum(fixed.values()), sum(var.values()), sum(v for _, v in full.values())
    bep_ratio = fixed_total / (max_tushum - var_total) if max_tushum > var_total else None

    def cost(k: str, q: float) -> float:
        return fixed.get(k, 0.0) + var.get(k, 0.0) * q

    # ── 8-9-ILOVA: kredit ──
    muddat = int(_num(p.get("muddat"), 120)) or 120
    imtiyoz = min(int(_num(p.get("imtiyoz"))), max(0, muddat - 1))
    foiz_pct = _num(p.get("foiz"), 18)
    loan = _loan(kredit, foiz_pct, muddat, imtiyoz, (p.get("kredit_turi") or "differensial").strip())

    # ── 11-14 ILOVA: yillik hisob ──
    soliq_turi = (p.get("soliq_turi") or "ytt").strip()
    tax_rate, tax_label, tax_rate_str = TAX_RATES.get(soliq_turi, TAX_RATES["ytt"])
    disc = _num(p.get("diskont"), DEFAULT_DISCOUNT_PCT) / 100
    Y = []
    for i, q in enumerate(cap):
        bevosita = cost("bevosita", q)
        agro_y = cost("agro", q)
        ijara_y, transport_y = cost("ijara", q), cost("transport", q)
        tannarx = bevosita + agro_y + cost("ishchi", q) + cost("ishchi_ijt", q) + cost("operatsion", q) + amort
        admin = cost("admin", q) + cost("admin_ijt", q)
        marketing = cost("marketing", q)
        boshqa = cost("kutilmagan", q) + cost("texnik", q) + cost("boshqa_admin", q)
        davr = admin + marketing + ijara_y + transport_y + boshqa
        yalpi = tushum[i] - tannarx
        op_foyda = yalpi - davr
        foiz = loan["foiz"][i]
        soliq = tushum[i] * tax_rate
        sof = op_foyda - foiz - soliq
        op_cf = op_foyda + amort
        sof_cf = op_cf - foiz - soliq
        qarz = loan["asosiy"][i]
        dscr = (op_cf - soliq) / (foiz + qarz) if (foiz + qarz) > 0 else None
        Y.append(dict(q=q, bevosita=bevosita, agro=agro_y, ijara=ijara_y, transport=transport_y, ishchi=cost("ishchi", q), ishchi_ijt=cost("ishchi_ijt", q),
                      kommunal=cost("operatsion", q), tannarx=tannarx, admin=admin, marketing=marketing,
                      boshqa=boshqa, davr=davr, yalpi=yalpi, op_foyda=op_foyda, foiz=foiz, soliq=soliq, sof=sof,
                      op_cf=op_cf, sof_cf=sof_cf, qarz=qarz, qarzdan_keyin=sof_cf - qarz, dscr=dscr))

    cf = [y["sof_cf"] for y in Y]  # soliq va kredit foizidan keyingi oqim (foydalanuvchi qarori)
    disc_cf = [c / (1 + disc) ** (t + 1) for t, c in enumerate(cf)]
    pv = sum(disc_cf)
    npv = pv - loyiha_qiymati
    npv_by_year = [sum(disc_cf[: n + 1]) - loyiha_qiymati for n in range(N_YEARS)]
    irr_v = irr([-loyiha_qiymati] + cf)
    pi = pv / loyiha_qiymati if loyiha_qiymati > 0 else 0.0
    pp = _payback(loyiha_qiymati, cf)
    dpp = _payback(loyiha_qiymati, disc_cf)
    roi = (sum(y["sof"] for y in Y) / N_YEARS) / loyiha_qiymati * 100 if loyiha_qiymati > 0 else 0.0
    dscr_vals = [y["dscr"] for y in Y if y["dscr"] is not None]
    if npv <= 0:
        warnings.insert(0, "DIQQAT: Loyiha o'zini oqlamaydi (NPV salbiy). Rentabellikni oshirish uchun "
                           "mahsulot/xizmat narxini ko'taring yoki xarajatlarni qisqartiring.")

    return dict(
        loyiha_qiymati=loyiha_qiymati, oz=oz, kredit=kredit, kredit_xarajat=kredit_xarajat, sugurta=sugurta,
        aylanma=aylanma, asosiy_oz=asosiy_oz, asosiy=asosiy, amort=amort,
        wages=dict(direktor=direktor, rahbar_oylik=rahbar_oylik, xodim=xodim, ishchi_oylik=ishchi_oylik,
                   yangi=yangi, yangi_oylik=yangi_oylik, admin=admin_wage, ishchi_wage=ishchi_wage,
                   yangi_wage=yangi_wage, prod=prod_wage, admin_ijt=admin_ijt, prod_ijt=prod_ijt),
        util_rows=util_rows, kommunal=kommunal, products=products, cap=cap, max_tushum=max_tushum,
        tushum=tushum, cogs_share=cogs_share, faoliyat=faoliyat, full=full, fixed=fixed, var=var, fixed_total=fixed_total, var_total=var_total,
        cost_total=cost_total, bep_ratio=bep_ratio, loan=loan, muddat=muddat, imtiyoz=imtiyoz,
        foiz_pct=foiz_pct, tax=(tax_rate, tax_label, tax_rate_str), disc=disc, years=Y, disc_cf=disc_cf,
        pv=pv, npv=npv, npv_by_year=npv_by_year, irr=irr_v, pi=pi, pp=pp, dpp=dpp, roi=roi,
        dscr_min=min(dscr_vals) if dscr_vals else None, warnings=warnings,
    )


def _yrs(vals) -> list:
    return [_r(v) for v in vals]


def _opt(Y: list[dict]) -> list[list]:
    """Ijara va transport: kiritilgan bo'lsa alohida qator."""
    rows = []
    if any(y["ijara"] for y in Y):
        rows.append(["Ijara xarajatlari", *_yrs(y["ijara"] for y in Y)])
    if any(y["transport"] for y in Y):
        rows.append(["Transport xarajatlari", *_yrs(y["transport"] for y in Y)])
    return rows


def build_tables(m: dict) -> list[dict]:
    Y, w = m["years"], m["wages"]
    yh = [f"{i + 1}-yil" for i in range(N_YEARS)]
    lq = m["loyiha_qiymati"] or 1
    fin_oz = m["kredit_xarajat"] + m["sugurta"]
    t = []
    t.append({"ilova": "1-ILOVA", "title": "LOYIHA QIYMATI",
              "headers": ["Ko'rsatkich", "O'z mablag'i (so'm)", "Bank krediti (so'm)", "Jami (so'm)", "Ulushi"],
              "rows": [
                  ["Asosiy vositalarni sotib olish (kredit hisobidan)", 0, _r(m["kredit"]), _r(m["kredit"]), _pct(m["kredit"] / lq)],
                  ["Asosiy vositalar (o'z mablag'i hisobidan)", _r(m["asosiy_oz"]), 0, _r(m["asosiy_oz"]), _pct(m["asosiy_oz"] / lq)],
                  ["JAMI asosiy vositalar", _r(m["asosiy_oz"]), _r(m["kredit"]), _r(m["asosiy"]), _pct(m["asosiy"] / lq)],
                  ["Aylanma kapital", _r(m["aylanma"]), 0, _r(m["aylanma"]), _pct(m["aylanma"] / lq)],
                  ["Sug'urta", _r(m["sugurta"]), 0, _r(m["sugurta"]), _pct(m["sugurta"] / lq)],
                  ["Kredit olish uchun boshqa xarajatlar (2%)", _r(m["kredit_xarajat"]), 0, _r(m["kredit_xarajat"]), _pct(m["kredit_xarajat"] / lq)],
                  ["LOYIHA QIYMATI", _r(m["oz"]), _r(m["kredit"]), _r(m["loyiha_qiymati"]), "100.0%"],
              ]})
    t.append({"ilova": "2-ILOVA", "title": "MOLIYAVIY REJA",
              "headers": ["Manba", "Summa (so'm)", "Ulushi"],
              "rows": [["O'z mablag'lari", _r(m["oz"]), _pct(m["oz"] / lq)],
                       ["Bank krediti", _r(m["kredit"]), _pct(m["kredit"] / lq)],
                       ["JAMI moliyalashtirish", _r(m["loyiha_qiymati"]), "100.0%"]]})
    t.append({"ilova": "3-ILOVA", "title": "LOYIHA ISHTIROKCHILARI XARAJATLARINING ULUSHI",
              "headers": ["Ko'rsatkich", "O'z mablag'i (so'm)", "Bank krediti (so'm)", "Jami (so'm)"],
              "rows": [["Asosiy vositalar", _r(m["asosiy_oz"]), _r(m["kredit"]), _r(m["asosiy"])],
                       ["Aylanma kapital", _r(m["aylanma"]), 0, _r(m["aylanma"])],
                       ["Moliyaviy xarajatlar (sug'urta, kredit olish)", _r(fin_oz), 0, _r(fin_oz)],
                       ["JAMI birinchi investitsiya xarajatlari", _r(m["oz"]), _r(m["kredit"]), _r(m["loyiha_qiymati"])]]})
    cum = [m["amort"] * (i + 1) for i in range(N_YEARS)]
    t.append({"ilova": "4-ILOVA", "title": "AMORTIZATSIYA HISOBI (10 yil, teng ulushda)",
              "headers": ["Ko'rsatkich", "Amortizatsiya bazasi (so'm)", "Stavka", *yh],
              "rows": [["Asosiy vositalar", _r(m["asosiy"]), "10.0%", *_yrs([m["amort"]] * N_YEARS)],
                       ["Jami amortizatsiya", "", "", *_yrs([m["amort"]] * N_YEARS)],
                       ["Yig'ilgan amortizatsiya", "", "", *_yrs(cum)]]})
    t.append({"ilova": "5-ILOVA", "title": "ISH HAQI XARAJATLARI",
              "headers": ["Lavozim", "Soni", "Maosh (so'm)", "Oylik jami (so'm)", "Yillik (so'm)"],
              "rows": [
                  ["Ma'muriyat: direktor", w["direktor"], _r(w["rahbar_oylik"]), _r(w["admin"] / 12), _r(w["admin"])],
                  ["Ijtimoiy soliq (12%)", "", "", "", _r(w["admin_ijt"])],
                  ["JAMI ma'muriyat", "", "", "", _r(w["admin"] + w["admin_ijt"])],
                  ["Ishchi xodimlar", w["xodim"], _r(w["ishchi_oylik"]), _r(w["ishchi_wage"] / 12), _r(w["ishchi_wage"])],
                  ["Yangi ishchi xodimlar", w["yangi"], _r(w["yangi_oylik"]), _r(w["yangi_wage"] / 12), _r(w["yangi_wage"])],
                  ["Ijtimoiy soliq (12%)", "", "", "", _r(w["prod_ijt"])],
                  ["JAMI ishchilar", w["xodim"] + w["yangi"], "", "", _r(w["prod"] + w["prod_ijt"])],
                  ["JAMI ISH HAQI FONDI", w["direktor"] + w["xodim"] + w["yangi"], "", "",
                   _r(w["admin"] + w["admin_ijt"] + w["prod"] + w["prod_ijt"])],
              ]})
    t.append({"ilova": "KOMMUNAL", "title": "FOYDALANISH XARAJATLARI",
              "headers": ["Bo'lim", "O'lchov birligi", "Yillik iste'mol", "Bir birlik narxi (so'm)", "Yillik xarajat (so'm)"],
              "rows": [*m["util_rows"], ["JAMI", "", "", "", _r(m["kommunal"])]]})
    prods = m["products"]
    t.append({"ilova": "6-ILOVA", "title": "XIZMAT KO'RSATISH VA SOTISH REJASI",
              "headers": ["Nomi", "O'lchov birligi", "Yillik hajm (to'liq quvvat)", "O'rtacha sotuv narxi (so'm)",
                          "1 yillik savdo tushumi (so'm)", "Tovar/xomashyo xarajati (so'm)", "Hisoblash usuli"],
              "rows": [*[[pr["nomi"], pr["olchov"], _r(pr["hajm"]), _r(pr["narx"]), _r(pr["hajm"] * pr["narx"]),
                          _r(pr["tannarx"]), pr["tannarx_usul"]] for pr in prods],
                       ["JAMI", "", "", "", _r(m["max_tushum"]), _r(sum(pr["tannarx"] for pr in prods)), ""]]})
    sales_rows = [["Quvvatlarni ishga tushirish", *[_pct(q) for q in m["cap"]]]]
    for pr in prods:
        sales_rows.append([f"{pr['nomi']}: hajm ({pr['olchov']})", *_yrs([pr["hajm"] * q for q in m["cap"]])])
        sales_rows.append([f"{pr['nomi']}: daromad (so'm)", *_yrs([pr["hajm"] * pr["narx"] * q for q in m["cap"]])])
    sales_rows.append(["JAMI SOTISH DAROMADLARI", *_yrs(m["tushum"])])
    t.append({"ilova": "6-ILOVA", "title": "SOTISH REJASI (10 yil)", "headers": ["Ko'rsatkich", *yh], "rows": sales_rows})
    tax_rate, tax_label, tax_rate_str = m["tax"]
    t.append({"ilova": "7-ILOVA", "title": "SOLIQ VA BOJLAR",
              "headers": ["Soliq turi", "Stavka", "Soliq solish obyekti", *yh],
              "rows": [[tax_label, tax_rate_str, "Sotishdan tushgan daromad", *_yrs(y["soliq"] for y in Y)],
                       ["JAMI SOLIQ VA BOJLAR", "", "", *_yrs(y["soliq"] for y in Y)]]})
    ln = m["loan"]
    t.append({"ilova": "8-9-ILOVA", "title": f"KREDIT TO'LOV GRAFIGI ({m['muddat']} oy, imtiyoz {m['imtiyoz']} oy, {m['foiz_pct']:g}%)",
              "headers": ["Davr", "Asosiy qarz to'lovi (so'm)", "Foiz to'lovi (so'm)", "Jami to'lov (so'm)", "Yil oxiri qoldiq (so'm)"],
              "rows": [*[[yh[i], _r(ln["asosiy"][i]), _r(ln["foiz"][i]), _r(ln["tolov"][i]), _r(ln["qoldiq"][i])] for i in range(N_YEARS)],
                       ["JAMI", _r(sum(ln["asosiy"])), _r(sum(ln["foiz"])), _r(sum(ln["tolov"])), ""]]})
    ct = m["cost_total"] or 1
    bep = m["bep_ratio"]
    t.append({"ilova": "10-ILOVA", "title": "TO'LIQ QUVVATDAGI XARAJATLAR VA ZARARSIZLIK NUQTASI",
              "headers": ["Xarajatlar", "To'liq xarajat (so'm)", "Doimiy (so'm)", "Doimiy %", "O'zgaruvchan (so'm)", "O'zgaruvchan %"],
              "rows": [*[[nomi, _r(v), _r(m["fixed"][k]), _pct(m["fixed"][k] / v if v else 0), _r(m["var"][k]), _pct(m["var"][k] / v if v else 0)]
                         for k, (nomi, v) in m["full"].items()],
                       ["JAMI XARAJATLAR", _r(m["cost_total"]), _r(m["fixed_total"]), _pct(m["fixed_total"] / ct), _r(m["var_total"]), _pct(m["var_total"] / ct)],
                       ["To'liq quvvatda sotish", _r(m["max_tushum"]), "", "", "", ""],
                       ["ZARARSIZLIK NUQTASI (quvvatdan)", _pct(bep) if bep is not None else "—", "", "", "", ""],
                       ["ZARARSIZLIK NUQTASI (so'm)", _r(bep * m["max_tushum"]) if bep is not None else "—", "", "", "", ""]]})
    t.append({"ilova": "11-ILOVA", "title": "TO'LIQ YILLIK XARAJATLAR",
              "headers": ["Xarajat moddalari", *yh],
              "rows": [["Rivojlanish quvvati", *[_pct(y["q"]) for y in Y]],
                       ["To'g'ridan-to'g'ri xarajatlar (tovar, xomashyo)", *_yrs(y["bevosita"] for y in Y)],
                       *([["Urug', yem, o'g'it va texnika", *_yrs(y["agro"] for y in Y)]] if any(y["agro"] for y in Y) else []),
                       ["Ishlab chiqarish xodimlarining ish haqi", *_yrs(y["ishchi"] for y in Y)],
                       ["Ijtimoiy soliq", *_yrs(y["ishchi_ijt"] for y in Y)],
                       ["Operatsion xarajatlar (kommunal)", *_yrs(y["kommunal"] for y in Y)],
                       ["Amortizatsiya", *_yrs([m["amort"]] * N_YEARS)],
                       ["TANNARX", *_yrs(y["tannarx"] for y in Y)],
                       ["Ma'muriy xarajatlar (ish haqi, ijtimoiy soliq)", *_yrs(y["admin"] for y in Y)],
                       ["Marketing xarajatlari", *_yrs(y["marketing"] for y in Y)],
                       *_opt(Y),
                       ["Boshqa xarajatlar", *_yrs(y["boshqa"] for y in Y)],
                       ["Davr xarajatlari", *_yrs(y["davr"] for y in Y)],
                       ["Operatsion xarajatlar", *_yrs(y["tannarx"] + y["davr"] for y in Y)],
                       ["Kredit foizlari", *_yrs(y["foiz"] for y in Y)],
                       ["SOTILGAN MAHSULOTLARNING XARAJATLARI", *_yrs(y["tannarx"] + y["davr"] + y["foiz"] for y in Y)]]})
    t.append({"ilova": "12-ILOVA", "title": "KUTILAYOTGAN FOYDA VA ZARAR",
              "headers": ["Ko'rsatkichlar", *yh],
              "rows": [["Sotishdan tushgan daromad", *_yrs(m["tushum"])],
                       ["Tannarx", *_yrs(y["tannarx"] for y in Y)],
                       ["Umumiy daromad (yalpi foyda)", *_yrs(y["yalpi"] for y in Y)],
                       ["Ma'muriy xarajatlar", *_yrs(y["admin"] for y in Y)],
                       ["Marketing xarajatlari", *_yrs(y["marketing"] for y in Y)],
                       *_opt(Y),
                       ["Boshqa xarajatlar", *_yrs(y["boshqa"] for y in Y)],
                       ["Operatsion foyda", *_yrs(y["op_foyda"] for y in Y)],
                       ["Moliyaviy xarajatlar (kredit foizi)", *_yrs(y["foiz"] for y in Y)],
                       ["Soliq to'laguncha foyda", *_yrs(y["op_foyda"] - y["foiz"] for y in Y)],
                       ["Soliqlar", *_yrs(y["soliq"] for y in Y)],
                       ["SOF FOYDA", *_yrs(y["sof"] for y in Y)],
                       ["Sof rentabellik", *[_pct(y["sof"] / t_) if t_ else "0.0%" for y, t_ in zip(Y, m["tushum"], strict=True)]],
                       ["Yalpi rentabellik", *[_pct(y["yalpi"] / t_) if t_ else "0.0%" for y, t_ in zip(Y, m["tushum"], strict=True)]]]})
    cum, c = [], 0.0
    for y in Y:
        c += y["qarzdan_keyin"]
        cum.append(c)
    t.append({"ilova": "13-ILOVA", "title": "PUL OQIMI",
              "headers": ["Ko'rsatkichlar", "0-yil", *yh],
              "rows": [["Sotishdan tushgan tushum", 0, *_yrs(m["tushum"])],
                       ["Xizmatning bevosita xarajatlari (tannarx)", 0, *_yrs(y["tannarx"] for y in Y)],
                       ["Yalpi pul tushumi", 0, *_yrs(y["yalpi"] for y in Y)],
                       ["Amortizatsiya (+)", 0, *_yrs([m["amort"]] * N_YEARS)],
                       ["Marketing xarajatlari", 0, *_yrs(y["marketing"] for y in Y)],
                       ["Ma'muriy xarajatlar", 0, *_yrs(y["admin"] for y in Y)],
                       *[[r[0], 0, *r[1:]] for r in _opt(Y)],
                       ["Boshqa xarajatlar", 0, *_yrs(y["boshqa"] for y in Y)],
                       ["Operatsion pul oqimi", 0, *_yrs(y["op_cf"] for y in Y)],
                       ["O'z mablag'lari", _r(m["oz"]), *[""] * N_YEARS],
                       ["Bank krediti", _r(m["kredit"]), *[""] * N_YEARS],
                       ["Investitsiyalar (loyiha qiymati)", _r(-m["loyiha_qiymati"]), *[""] * N_YEARS],
                       ["Foiz to'lovlari", 0, *_yrs(y["foiz"] for y in Y)],
                       ["Soliqlar", 0, *_yrs(y["soliq"] for y in Y)],
                       ["SOF PUL OQIMI", 0, *_yrs(y["sof_cf"] for y in Y)],
                       ["Asosiy qarz to'lovi", 0, *_yrs(y["qarz"] for y in Y)],
                       ["Kredit to'langanidan keyin naqd pul", 0, *_yrs(y["qarzdan_keyin"] for y in Y)],
                       ["Kumulyativ pul oqimi", 0, *_yrs(cum)],
                       ["Qarzga xizmat ko'rsatish koeffitsienti (DSCR)", "", *[f"{y['dscr']:.2f}" if y["dscr"] is not None else "—" for y in Y]]]})
    rate_pct = f"{m['disc'] * 100:g}%"
    irr_v = m["irr"]
    t.append({"ilova": "14-ILOVA", "title": "NPV, IRR, DPP, PI HISOBI",
              "headers": ["Davr", "Sof pul oqimi (soliq va foizdan keyin)", f"Diskontlangan oqim ({rate_pct})", "Sof hozirgi qiymat (NPV)"],
              "rows": [["0-yil", _r(-m["loyiha_qiymati"]), _r(-m["loyiha_qiymati"]), _r(-m["loyiha_qiymati"])],
                       *[[yh[i], _r(Y[i]["sof_cf"]), _r(m["disc_cf"][i]), _r(m["npv_by_year"][i])] for i in range(N_YEARS)],
                       ["", "", "", ""],
                       ["SOF HOZIRGI QIYMAT (NPV, 10 yil)", "", "", _r(m["npv"])],
                       ["Ichki daromadlilik darajasi (IRR)", "", "", f"{irr_v * 100:.1f}%" if irr_v is not None else "—"],
                       ["Daromadlilik indeksi (PI)", "", "", f"{m['pi']:.2f}"],
                       ["Investitsiyaning qaytarilish muddati (PP)", "", "", f"{m['pp']:.1f} yil" if m["pp"] is not None else "10 yildan ortiq"],
                       ["Diskontlangan qaytarilish muddati (DPP)", "", "", f"{m['dpp']:.1f} yil" if m["dpp"] is not None else "10 yildan ortiq"]]})
    return t

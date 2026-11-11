"""Moliyaviy model "Asosiy shablon npv 10 yillik.xls" bilan mosligi (docs/EXCEL_SHABLON_TAHLILI.md)."""
import pytest

from app.engine.financial_engine import calculate_financial_model
from app.engine.template_model import build_model
from tests.conftest import PLAN_INPUT

# Excel shablonidagi kirish qiymatlari
EXCEL_INPUT = {
    "faoliyat_turi": "savdo", "loyiha_nomi": "Oziq-ovqat tovarlari chakana savdosi", "soliq_turi": "mchj",
    "oz_mablag": 45_588_000, "kredit": 100_000_000, "loyiha_qiymati": 145_588_000,
    "foiz": 18, "muddat": 120, "imtiyoz": 24, "kredit_turi": "differensial",
    "hajm": 32_000, "narx": 15_000,
    "direktor": 1, "rahbar_oylik": 5_500_000, "xodim": 3, "ishchi_oylik": 1_880_000,
    "yangi_xodim": 2, "yangi_ishchi_oylik": 1_880_000,
    "elektr": 100, "boshqa_kommunal": 5_000_000,  # 1200 kVt/yil x 900 + 5 mln
    "tannarx_ulushi": 1,  # shablondagi "to'g'ridan-to'g'ri xarajatlar" = tushumning 1%
}
CAP = [0.75, 0.77, 0.80, 0.82, 0.85, 0.90, 0.92, 0.95, 1.00, 1.00]
# Yagona ataylab farq: Excel 1% ning 80% ini doimiy deb oladi (3,84 mln quvvatdan qat'i nazar),
# kodda tovar/xomashyo sotuvga to'liq proporsional. Farq = 3,84 mln x (1 - quvvat).
SHIFT = [3_840_000 * (1 - q) for q in CAP]
# Excel qiymatlari (ProfLoss!C17:L17, ProfLoss!C7:L7, CashFlow!D14:M14, CostTotal!F19)
EXCEL_NET = [102884381.1, 108724159.57, 118515077.28, 126604855.75, 137614523.46,
             154463969.64, 162553748.11, 173563415.82, 190412862.0, 192662862.0]
EXCEL_TANNARX = [119294800, 121877200, 125750800, 128333200, 132206800,
                 138662800, 141245200, 145118800, 151574800, 151574800]
EXCEL_OPCF = [178443181.1, 185434959.57, 195922627.28, 202914405.75, 213402073.46,
              230881519.64, 237873298.11, 248360965.82, 265840412, 265840412]
EXCEL_SOF_CF = [117243181.1, 123082959.57, 132873877.28, 140963655.75, 151973323.46,
                168822769.64, 176912548.11, 187922215.82, 204771662.0, 207021662.0]


def test_matches_excel_template_yearly_values():
    m = build_model(EXCEL_INPUT)
    for i, y in enumerate(m["years"]):
        assert y["sof"] == pytest.approx(EXCEL_NET[i] + SHIFT[i], abs=0.01)
        assert y["tannarx"] == pytest.approx(EXCEL_TANNARX[i] - SHIFT[i], abs=0.01)
        assert y["op_cf"] == pytest.approx(EXCEL_OPCF[i] + SHIFT[i], abs=0.01)
    # CostTotal: doimiy 98 107 311,6 va o'zgaruvchan 130 411 076,4 dan 3,84 mln ko'chadi
    assert m["bep_ratio"] == pytest.approx(94_267_311.6 / (480_000_000 - 134_251_076.4), rel=1e-12)


def test_excel_errors_are_corrected():
    m = build_model(EXCEL_INPUT)
    # Loyiha qiymati: moliyaviy xarajat bir marta (Excel: 147 588 000)
    assert m["loyiha_qiymati"] == 145_588_000
    assert m["kredit_xarajat"] == 2_000_000
    # NPV: Excel'ning sof pul oqimi qatori (CashFlow!D20:M20, soliq va foizdan keyin), 14%, 10 yil
    pv = sum((v + SHIFT[t]) / 1.14 ** (t + 1) for t, v in enumerate(EXCEL_SOF_CF))
    assert m["npv"] == pytest.approx(pv - 145_588_000, abs=0.01)
    for t, y in enumerate(m["years"]):
        assert y["sof_cf"] == pytest.approx(EXCEL_SOF_CF[t] + SHIFT[t], abs=0.01)
    # Asosiy qarz jadvaldan: 2 yil imtiyoz, keyin 12,5 mln/yil, jami = kredit (Excel: 162,5 mln)
    assert [round(v) for v in m["loan"]["asosiy"]] == [0, 0] + [12_500_000] * 8
    # PI = PV / investitsiya; PP va DPP hisoblanadi
    assert m["pi"] == pytest.approx((m["npv"] + m["loyiha_qiymati"]) / m["loyiha_qiymati"])
    assert 0 < m["pp"] < m["dpp"] < 2


def test_social_tax_counted_once():
    model = calculate_financial_model(EXCEL_INPUT)
    taxes = next(t for t in model["tables"] if t["ilova"] == "7-ILOVA")
    assert [r[0] for r in taxes["rows"]] == ["Yagona soliq to'lovi", "JAMI SOLIQ VA BOJLAR"]
    assert taxes["rows"][0][3] == 43_200_000  # 12% x 360 mln


def test_unit_cost_and_ytt_tax():
    base = build_model({**EXCEL_INPUT, "soliq_turi": "ytt"})
    with_cost = build_model({**EXCEL_INPUT, "soliq_turi": "ytt", "xomashyo_narx": 10_000})
    assert base["years"][0]["soliq"] == pytest.approx(360_000_000 * 0.04)
    # 1-yil: 24 000 birlik x 10 000 = 240 mln (birlik narxi ulushdan ustun)
    assert with_cost["years"][0]["bevosita"] == pytest.approx(240_000_000)
    assert with_cost["npv"] < base["npv"]


@pytest.mark.parametrize("faoliyat,share", [("savdo", 0.75), ("ishlab_chiqarish", 0.55),
                                            ("qishloq_xojaligi", 0.40), ("xizmat", 0.15)])
def test_default_goods_cost_by_activity(faoliyat, share):
    inp = {k: v for k, v in EXCEL_INPUT.items() if k != "tannarx_ulushi"}
    m = build_model({**inp, "faoliyat_turi": faoliyat})
    assert m["years"][0]["bevosita"] == pytest.approx(360_000_000 * share)
    assert m["years"][9]["bevosita"] == pytest.approx(480_000_000 * share)


def test_rent_transport_agro_are_separate_lines():
    inp = {k: v for k, v in EXCEL_INPUT.items() if k != "tannarx_ulushi"}
    model = calculate_financial_model({**inp, "faoliyat_turi": "qishloq_xojaligi", "dokon_ijarasi": 2_000_000,
                                       "yer_ijarasi": 6_000_000, "transport_xarajat": 1_000_000,
                                       "urug_yem_narx": 50_000_000, "texnika_xarajat": 10_000_000, "gaz": 100})
    tables = {t["title"]: t for t in model["tables"]}
    pl = [r[0] for r in tables["KUTILAYOTGAN FOYDA VA ZARAR"]["rows"]]
    assert "Ijara xarajatlari" in pl and "Transport xarajatlari" in pl
    costs = {r[0]: r for r in tables["TO'LIQ YILLIK XARAJATLAR"]["rows"]}
    assert costs["Urug', yem, o'g'it va texnika"][1] == 60_000_000 * 0.75
    assert costs["To'g'ridan-to'g'ri xarajatlar (tovar, xomashyo)"][1] == 0  # urug'/yem kiritilgan
    assert tables["KUTILAYOTGAN FOYDA VA ZARAR"]["rows"][pl.index("Ijara xarajatlari")][1] == 30_000_000
    assert tables["KUTILAYOTGAN FOYDA VA ZARAR"]["rows"][pl.index("Transport xarajatlari")][1] == pytest.approx(
        12_000_000 * (0.7 + 0.3 * 0.75))
    util = [r[0] for r in tables["FOYDALANISH XARAJATLARI"]["rows"]]
    assert "Tabiiy gaz" in util


def test_multiple_products_and_overrides():
    m = build_model({**EXCEL_INPUT, "hajm": None, "narx": None, "diskont": 20, "quvvat": [100] * 10,
                     "mahsulotlar": [{"nomi": "Non", "hajm": 1000, "narx": 5000},
                                     {"nomi": "Somsa", "hajm": 2000, "narx": 4000, "xomashyo_narx": 1500}]})
    assert m["max_tushum"] == 13_000_000
    assert m["tushum"] == [13_000_000] * 10
    assert m["disc"] == 0.2
    # Non: 5 mln x 1% (ulush), Somsa: 2000 x 1500 (birlik narxi)
    assert m["full"]["bevosita"][1] == pytest.approx(5_000_000 * 0.01 + 3_000_000)


async def test_api_accepts_products_and_validates(client):
    payload = {k: v for k, v in PLAN_INPUT.items() if k not in ("hajm", "narx")}
    r = await client.post("/v1/plans/preview", json=payload)
    assert r.status_code == 422 and "mahsulotlar" in r.text
    payload["mahsulotlar"] = [{"nomi": "Non", "hajm": 2500, "narx": 120000}]
    r = await client.post("/v1/plans/preview", json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["indicators"]["npv"] != 0
    payload["quvvat"] = [75] * 9
    assert (await client.post("/v1/plans/preview", json=payload)).status_code == 422


@pytest.mark.parametrize("muddat,years", [(36, 3), (30, 3), (12, 1), (60, 5), (120, 10), (180, 10), (None, 10)])
def test_horizon_follows_loan_term(muddat, years):
    """Loyiha davri kredit muddatiga moslashadi: 36 oy -> 3 yil, qolgan yillar jadvallarda yo'q."""
    data = {**EXCEL_INPUT, "imtiyoz": 0, "muddat": muddat}
    res = calculate_financial_model(data)
    m = build_model(data)
    assert m["n_years"] == years and len(m["years"]) == years and len(m["cap"]) == years
    assert res["indicators"]["loyiha_yillari"] == years
    for t in res["tables"]:
        yil_cols = [h for h in t.get("headers", []) if str(h).endswith("-yil") and h != "0-yil"]
        assert yil_cols in ([], [f"{i + 1}-yil" for i in range(years)]), t["title"]
    if muddat and muddat <= 120:
        assert sum(m["loan"]["asosiy"]) == pytest.approx(EXCEL_INPUT["kredit"])  # kredit davr ichida to'liq qaytadi
        assert m["loan"]["qoldiq"][-1] == pytest.approx(0, abs=0.01)


def test_short_horizon_metrics_use_only_those_years():
    long_ = build_model({**EXCEL_INPUT, "muddat": 120, "imtiyoz": 0})
    short = build_model({**EXCEL_INPUT, "muddat": 36, "imtiyoz": 0})
    assert len(short["npv_by_year"]) == 3 and short["npv"] == pytest.approx(short["npv_by_year"][-1])
    assert short["npv"] < long_["npv"]
    assert any("36 oy (3 yil)" in w for w in short["warnings"])
    assert not any("Loyiha davri" in w for w in long_["warnings"])
    # quvvat grafigi 10 qiymat bilan kelsa ham faqat 3 yili olinadi
    custom = build_model({**EXCEL_INPUT, "muddat": 36, "quvvat": [50, 60, 70, 80, 90, 100, 100, 100, 100, 100]})
    assert custom["cap"] == [0.5, 0.6, 0.7]


def test_amortization_spread_over_loan_term():
    """Asosiy vositalar kredit muddatida to'liq amortizatsiya qilinadi: 36 oy -> 3 yilga teng."""
    short = build_model({**EXCEL_INPUT, "muddat": 36, "imtiyoz": 0})
    long_ = build_model({**EXCEL_INPUT, "muddat": 120, "imtiyoz": 0})
    assert short["amort"] == pytest.approx(short["asosiy"] / 3)
    assert short["amort"] * 3 == pytest.approx(short["asosiy"])
    assert long_["amort"] == pytest.approx(long_["asosiy"] / 10)  # Excel: 10%
    # ta'mirlash xarajati amortizatsiya davriga bog'liq emas
    assert short["full"]["texnik"][1] == pytest.approx(long_["full"]["texnik"][1])
    res = calculate_financial_model({**EXCEL_INPUT, "muddat": 36, "imtiyoz": 0})
    t4 = next(t for t in res["tables"] if t["ilova"] == "4-ILOVA")
    assert t4["title"].endswith("(3 yil, teng ulushda)") and t4["rows"][0][2] == "33.3%"
    assert t4["rows"][2][-1] == pytest.approx(round(short["asosiy"], 2), abs=0.05)  # 3-yil oxirida to'liq

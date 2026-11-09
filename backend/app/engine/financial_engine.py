import os
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from app.engine.template_model import build_model, build_tables


FAOLIYAT_NOMLARI = {
    "ishlab_chiqarish": "Ishlab chiqarish",
    "qishloq_xojaligi": "Qishloq xo'jaligi",
    "savdo": "Savdo bizneslari",
    "xizmat": "Xizmat ko'rsatish",
}

def calculate_financial_model(payload: dict) -> dict:
    """10 yillik model: hisob-kitob "Asosiy shablon npv 10 yillik.xls" asosida (template_model.py)."""
    faoliyat_turi = (payload.get("faoliyat_turi") or "ishlab_chiqarish").strip()
    faoliyat_nomi = FAOLIYAT_NOMLARI.get(faoliyat_turi, "Ishlab chiqarish")
    m = build_model(payload)
    tables = build_tables(m)
    products = m["products"]
    jami_hajm = sum(pr["hajm"] for pr in products)
    irr_pct = round(m["irr"] * 100, 2) if m["irr"] is not None else 0.0
    payback = round(m["pp"], 2) if m["pp"] is not None else 0.0
    warning = " ".join(m["warnings"])
    w = m["wages"]

    def s(key: str, default: str = "") -> str:
        return (payload.get(key) or default).strip()

    context = {
        "bank": s("bank"),
        "berilgan_vaqti": payload.get("ro_sana") or datetime.now().strftime("%d.%m.%Y"),
        "direktor": w["direktor"],
        "discount_rate": round(m["disc"] * 100, 2),
        "elektr": payload.get("elektr") or 0,
        "faoliyat": payload.get("faoliyat_turi_text") or "",
        "faoliyat_turi": faoliyat_turi,
        "faoliyat_turi_nomi": faoliyat_nomi,
        "fio": s("fio"),
        "foiz": m["foiz_pct"],
        "gaz": payload.get("gaz") or 0,
        "hajm": jami_hajm,
        "imtiyoz": m["imtiyoz"],
        "irr": irr_pct,
        "ishchi_oylik": w["ishchi_oylik"],
        "jshshir": s("jshshir"),
        "kredit": m["kredit"],
        "kredit_turi": s("kredit_turi", "differensial"),
        "loyiha_nomi": s("loyiha_nomi"),
        "loyiha_qiymati": m["loyiha_qiymati"],
        "mahsulot": ", ".join(pr["nomi"] for pr in products) or s("loyiha_nomi"),
        "manzil": s("manzil"),
        "muddat": m["muddat"],
        "mulk": s("mulk"),
        "narx": round(m["max_tushum"] / jami_hajm, 2) if jami_hajm else 0,
        "npv": round(m["npv"], 2),
        "olchov": products[0]["olchov"] if products else "dona",
        "oqava": payload.get("oqava") or 0,
        "oz_mablag": m["oz"],
        "pasport": "",
        "payback": payback,
        "pi": round(m["pi"], 4),
        "rahbar_oylik": w["rahbar_oylik"],
        "roi": round(m["roi"], 2),
        "soliq_turi": s("soliq_turi", "ytt"),
        "stir": s("stir"),
        "suv": payload.get("suv") or 0,
        "tashabbuskor": s("tashabbuskor"),
        "warning": warning,
        "xodim": w["xodim"],
        "yangi_ishchi_oylik": w["yangi_oylik"],
        "yangi_xodim": w["yangi"],
        "yillik_daromad": round(m["tushum"][0], 2),
        "yillik_sof_foyda": round(m["years"][0]["sof"], 2),
    }
    indicators = {
        "discount_rate": round(m["disc"] * 100, 2),
        "irr": irr_pct,
        "jami_daromad": round(sum(m["tushum"]), 2),
        "jami_sof_foyda": round(sum(y["sof"] for y in m["years"]), 2),
        "kredit": m["kredit"],
        "loyiha_qiymati": m["loyiha_qiymati"],
        "npv": round(m["npv"], 2),
        "oz_mablag": m["oz"],
        "payback": payback,
        "dpp": round(m["dpp"], 2) if m["dpp"] is not None else 0.0,
        "pi": round(m["pi"], 4),
        "roi": round(m["roi"], 2),
        "dscr_min": round(m["dscr_min"], 2) if m["dscr_min"] is not None else None,
        "zararsizlik_nuqtasi": round(m["bep_ratio"] * 100, 1) if m["bep_ratio"] is not None else None,
        "warning": warning,
    }
    return {"context": context, "faoliyat_nomi": faoliyat_nomi, "faoliyat_turi": faoliyat_turi,
            "indicators": indicators, "tables": tables}


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

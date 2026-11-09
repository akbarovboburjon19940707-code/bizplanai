"""Biznes-reja Word hujjatini shablon asosida yaratish (templates/biznes_reja.docx).

Shablon: scripts/build_word_template.py (asl template.docx dan), tahlil: docs/WORD_SHABLON_TAHLILI.md.
Belgilar:
  {{kalit}}            matn ichida; run'larga bo'lingan bo'lsa ham bir martalik almashtiriladi
  {{matn:kalit}}       paragraf o'rniga 0..N paragraf (formati saqlanadi)
  {{jadval:ILOVA}}     paragraf o'rniga moliyaviy jadval(lar)
  {{ilovalar}}         barcha ilovalar, yangi albom (landscape) bo'limda
Foydalanuvchi matni qayta ishlanmaydi: qo'yilgan qiymat ichidagi "{{...}}" belgi bo'lib qolmaydi.
"""
from __future__ import annotations

import copy
import os
import re
from collections import defaultdict
from datetime import datetime

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.table import Table

from app.engine.word_texts import COMMON_TALAB, RISKS, TEXTS

TEMPLATE = os.path.join(os.path.dirname(__file__), "templates", "biznes_reja.docx")
PH = re.compile(r"\{\{\s*([\w:.\-]+)\s*\}\}")
BLANK = "____________________"
PORTRAIT_CM, LANDSCAPE_CM = 17.0, 25.5  # A4, 1.9 sm chetlar
TOTAL_RE = re.compile(r"^(JAMI|SOF|LOYIHA QIYMATI|TANNARX|ZARARSIZLIK|SOTILGAN)", re.I)
INLINE_TABLES = {  # shablondagi jadval o'rni -> qaysi ilova jadvallari (birinchisi yoki hammasi)
    "1-ILOVA": 1, "5-ILOVA": 1, "6-ILOVA": 1, "10-ILOVA": 1, "KOMMUNAL": 1,
}


# ── Format yordamchilari ──
def _money(v) -> str:
    try:
        return f"{float(v):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return str(v or "")


def _plain(v) -> str:
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _cell_text(v) -> str:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return _money(v)
    return "" if v is None else str(v)


# ── XML darajasidagi amallar ──
def _texts(p_el) -> list:
    return p_el.xpath(".//w:t")


def _set_para_text(p_el, text: str) -> None:
    ts = _texts(p_el)
    if not ts:
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        r.append(t)
        p_el.append(r)
        ts = [t]
    ts[0].text = text
    ts[0].set(qn("xml:space"), "preserve")
    for t in ts[1:]:
        t.text = ""


def _replace_inline(p_el, values: dict[str, str]) -> None:
    ts = _texts(p_el)
    if not ts:
        return
    full = "".join(t.text or "" for t in ts)
    if "{{" not in full:
        return
    bounds, pos = [], 0
    for t in ts:
        bounds.append((pos, pos + len(t.text or "")))
        pos += len(t.text or "")

    def locate(i: int, end: bool = False) -> int:
        for k, (a, b) in enumerate(bounds):
            if a <= i < b or (end and a < i <= b):
                return k
        return len(ts) - 1

    for m in reversed(list(PH.finditer(full))):
        value = values.get(m.group(1), "")
        s, e = m.start(), m.end()
        ks, ke = locate(s), locate(e, end=True)
        a_s, a_e = bounds[ks][0], bounds[ke][0]
        ts_s, ts_e = ts[ks], ts[ke]
        if ks == ke:
            txt = ts_s.text or ""
            ts_s.text = txt[: s - a_s] + value + txt[e - a_s:]
        else:
            ts_s.text = (ts_s.text or "")[: s - a_s] + value
            for k in range(ks + 1, ke):
                ts[k].text = ""
            ts_e.text = (ts_e.text or "")[e - a_e:]
        ts_s.set(qn("xml:space"), "preserve")


def _expand_block(p_el, items: list[str]) -> None:
    """Paragrafni items soniga ko'ra nusxalaydi (bo'sh bo'lsa o'chiradi; katakda bitta bo'sh qoladi)."""
    parent = p_el.getparent()
    for text in items:
        new = copy.deepcopy(p_el)
        _set_para_text(new, text)
        p_el.addprevious(new)
    if items or parent.tag != qn("w:tc") or len(parent.findall(qn("w:p"))) > 1:
        parent.remove(p_el)
    else:
        _set_para_text(p_el, "")


def _shade(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def _build_table(doc, headers: list, rows: list[list], font_size: float, width_cm: float) -> Table:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = doc.styles["Table Grid"]
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    n = len(headers)
    first = width_cm * (0.34 if n <= 6 else 0.18)  # birinchi ustun (nomlar) kengroq
    widths = [Cm(first)] + [Cm((width_cm - first) / max(1, n - 1))] * (n - 1)

    def fill(cell, value, bold=False, align=None):
        cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0)
        if align is not None:
            p.alignment = align
        run = p.add_run(_cell_text(value))
        run.font.size = Pt(font_size)
        run.font.name = "Times New Roman"
        run.bold = bold

    for i, h in enumerate(headers):
        fill(table.rows[0].cells[i], h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
        _shade(table.rows[0].cells[i], "D9E2F3")
    _repeat_header(table.rows[0])
    for cell in table.rows[0].cells:  # sarlavha qatori birinchi ma'lumot qatoridan ajralmasin
        cell.paragraphs[0].paragraph_format.keep_with_next = True
    for row in rows:
        total = bool(row) and bool(TOTAL_RE.match(str(row[0])))
        cells = table.add_row().cells
        for i, v in enumerate(row[: len(headers)]):
            numeric = isinstance(v, (int, float)) and not isinstance(v, bool)
            fill(cells[i], v, bold=total,
                 align=WD_ALIGN_PARAGRAPH.RIGHT if numeric else (WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER))
            if total:
                _shade(cells[i], "FEF3C7")
    for row in table.rows:
        for cell, w in zip(row.cells, widths, strict=True):
            cell.width = w
    return table


def _repeat_header(row) -> None:
    """Jadval keyingi betga o'tsa sarlavha qatori takrorlanadi."""
    tr_pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def _new_paragraph(doc, text: str = "", bold: bool = False, size: float = 11, center: bool = False,
                   page_break: bool = False):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)
    if page_break:
        p.add_run().add_break(WD_BREAK.PAGE)
    if text:
        r = p.add_run(text)
        r.bold = bold
        r.font.size = Pt(size)
        r.font.name = "Times New Roman"
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def _landscape_from_here(doc, anchor_el) -> None:
    """anchor_el dan oldin bo'limni yopadi (kitob shakli), keyingi qism albom shaklida."""
    body = doc.element.body
    body_sect = body.find(qn("w:sectPr"))
    # python-docx add_section_break bilan bir xil: rsid'siz nusxa (aks holda Word faylni "buzilgan" deydi),
    # oxirgi bo'lim header/footer'ni oldingisidan meros oladi
    p = OxmlElement("w:p")
    p_pr = OxmlElement("w:pPr")
    p_pr.append(body_sect.clone())
    p.append(p_pr)
    anchor_el.addprevious(p)
    for ref in body_sect.xpath("w:headerReference|w:footerReference"):
        body_sect.remove(ref)
    pg = body_sect.find(qn("w:pgSz"))
    w, h = pg.get(qn("w:w")), pg.get(qn("w:h"))
    pg.set(qn("w:w"), h)
    pg.set(qn("w:h"), w)
    pg.set(qn("w:orient"), "landscape")
    title_pg = body_sect.find(qn("w:titlePg"))
    if title_pg is not None:  # muqova headeri faqat 1-betda
        body_sect.remove(title_pg)


# ── Ma'lumotlar ──
def _activity_values(ctx: dict, ind: dict, ai: dict[str, dict] | None) -> tuple[dict, dict]:
    from app.engine.word_generator import generate_swot_and_market_analysis

    faoliyat = ctx.get("faoliyat_turi") or "ishlab_chiqarish"
    tx = TEXTS.get(faoliyat, TEXTS["ishlab_chiqarish"])
    fmt = defaultdict(str, {
        "loyiha_nomi": ctx.get("loyiha_nomi") or "Loyiha",
        "tashabbuskor": ctx.get("tashabbuskor") or "Tadbirkor",
        "manzil": ctx.get("manzil") or "loyiha joylashgan",
        "mahsulot": ctx.get("mahsulot") or ctx.get("loyiha_nomi") or "mahsulot",
    })

    def f(s: str) -> str:
        return s.format_map(fmt)

    market = generate_swot_and_market_analysis(ctx)
    swot = market["swot"]
    marks = {"strengths": 2, "weaknesses": 1, "opportunities": 2, "threats": 1}
    lists = {k: [f"{item}{' ++' if i < marks[k] else ''}" for i, item in enumerate(swot[k])] for k in marks}
    n = {k: len(v) for k, v in lists.items()}
    imp = {k: min(marks[k], n[k]) for k in marks}

    def cmp(a: int, b: int, x: str, y: str) -> str:
        return f"{x} > {y}" if a > b else (f"{x} = {y}" if a == b else f"{x} < {y}")

    blocks: dict[str, list[str]] = {
        "rasm": [],
        "maqsad": [f(t) for t in tx["maqsad"]],
        "resurs": [f(tx["resurs"])],
        "talab": [COMMON_TALAB],
        "raqobat": [f(t) for t in tx["raqobat"]],
        "ekologiya": [f(tx["ekologiya"])],
        "loyiha_maqsadi": [],
        "bozor_tahlili": [market["market_demand"], market["pricing"]],
        "marketing_rejasi": ["Korxonaning raqobat ustunliklari:", *market["advantages"]],
        "risk_tahlili": ["Asosiy risklar va ularni kamaytirish choralari:", *[f"{r}: {m}" for r, m in RISKS]],
        "swot_tahlili": [],
        "texnik_tahlil": [],
        "swot_s": lists["strengths"], "swot_w": lists["weaknesses"],
        "swot_o": lists["opportunities"], "swot_t": lists["threats"],
        "swot_c0": ["Kuchli tomonlar", f"{n['strengths']} ta", "Kuchsiz tomonlar", f"{n['weaknesses']} ta"],
        "swot_c1": [cmp(n["strengths"], n["weaknesses"], "S", "W")],
        "swot_c2": ["++ S", f"{imp['strengths']} ta", "++ W", f"{imp['weaknesses']} ta"],
        "swot_c3": [cmp(imp["strengths"], imp["weaknesses"], "++S", "++W")],
        "swot_c4": ["Imkoniyatlar", f"{n['opportunities']} ta", "Tahdidlar", f"{n['threats']} ta"],
        "swot_c5": [cmp(n["opportunities"], n["threats"], "O", "T")],
        "swot_c6": ["++ O", f"{imp['opportunities']} ta", "++ T", f"{imp['threats']} ta"],
        "swot_c7": [cmp(imp["opportunities"], imp["threats"], "++O", "++T")],
    }
    for key, item in (ai or {}).items():  # AI matni bo'lsa standart matn o'rniga
        text = (item or {}).get("text") if isinstance(item, dict) else item
        if text and key in blocks:
            blocks[key] = [p.strip() for p in str(text).split("\n") if p.strip()]

    direktor, xodim, yangi = (int(ctx.get(k) or 0) for k in ("direktor", "xodim", "yangi_xodim"))
    shtat = (f"Korxonada jami {direktor + xodim + yangi} nafar xodim faoliyat ko‘rsatadi: {direktor} nafar rahbar va "
             f"{xodim + yangi} nafar ishchi.")
    if yangi:
        shtat += f" Shundan {yangi} nafari uchun loyiha doirasida yangi ish o‘rni tashkil etiladi."
    blocks["shtat"] = [shtat]
    blocks["xulosa"] = _xulosa(ind)

    scalars = {"soha_nomi": tx["soha_nomi"], "bino_turi": tx["bino_turi"]}
    p4 = {f"p4_{k}": f(v) for k, v in tx["p4"].items()}
    segs = {f"seg{i + 1}_{k}": f(v) for i, s in enumerate(tx["segments"]) for k, v in s.items()}
    return {**scalars, **p4, **segs}, blocks


def _xulosa(ind: dict) -> list[str]:
    npv = float(ind.get("npv") or 0)
    irr = ind.get("irr")
    pp = ind.get("payback") or 0
    dscr = ind.get("dscr_min")
    if npv > 0:
        parts = [f"sof joriy qiymat (NPV) {_money(npv)} so‘m"]
        if irr:
            parts.append(f"ichki daromadlilik darajasi (IRR) {float(irr):.1f}%")
        if pp:
            parts.append(f"investitsiyalarni qoplash muddati {float(pp):.1f} yil")
        if dscr:
            parts.append(f"qarzga xizmat ko‘rsatish koeffitsienti (DSCR) eng kamida {float(dscr):.2f}")
        return [
            "Tahlillar natijasida loyiha moliyaviy jihatdan samarali ekani aniqlandi: " + ", ".join(parts) + ".",
            "Loyihadan tushadigan pul oqimi kredit va uning foizlarini belgilangan muddatlarda qaytarish imkonini beradi. "
            "Shu asosda loyihani moliyalashtirish maqsadga muvofiq deb hisoblanadi.",
        ]
    return [
        f"Kiritilgan ma’lumotlar bilan loyiha yetarli darajada samarali emas: sof joriy qiymat (NPV) {_money(npv)} so‘m.",
        "Loyihani moliyalashtirishdan oldin sotish hajmi va narxlarni qayta ko‘rib chiqish, xarajatlarni kamaytirish "
        "yoki kredit shartlarini o‘zgartirish tavsiya etiladi.",
    ]


def _scalars(ctx: dict) -> dict[str, str]:
    def s(key: str, blank: bool = True) -> str:
        v = ctx.get(key)
        if v is None or v == "":
            return BLANK if blank else ""
        return str(v).strip()

    now = datetime.now()
    return {
        "tashabbuskor": s("tashabbuskor"), "fio": s("fio"), "loyiha_nomi": s("loyiha_nomi"),
        "manzil": s("manzil"), "bank": s("bank"), "stir": s("stir"), "jshshir": s("jshshir"),
        "pasport": s("pasport"), "pasport_berilgan": BLANK,
        "faoliyat": s("faoliyat") if ctx.get("faoliyat") else ctx.get("faoliyat_turi_nomi") or BLANK,
        "mulk": s("mulk"),
        "loyiha_qiymati": _money(ctx.get("loyiha_qiymati")), "oz_mablag": _money(ctx.get("oz_mablag")),
        "kredit": _money(ctx.get("kredit")), "muddat": _plain(ctx.get("muddat") or 0),
        "imtiyoz": _plain(ctx.get("imtiyoz") or 0), "foiz": _plain(ctx.get("foiz") or 0),
        "yil": str(now.year), "sana": now.strftime("%d.%m.%Y"),
    }


# ── Asosiy funksiya ──
def render_plan_docx(model_data: dict, output_path: str, ai_sections: dict | None = None) -> str:
    ctx = model_data.get("context", {})
    ind = model_data.get("indicators", {})
    tables = model_data.get("tables", [])
    doc = Document(TEMPLATE)

    extra, blocks = _activity_values(ctx, ind, ai_sections)
    values = {**_scalars(ctx), **extra}
    by_ilova: dict[str, list[dict]] = defaultdict(list)
    for t in tables:
        by_ilova[t.get("ilova", "")].append(t)

    parts = [doc.element.body]
    for s in doc.sections:
        for hf in (s.header, s.footer, s.first_page_header, s.first_page_footer):
            if not hf.is_linked_to_previous and hf._element not in parts:
                parts.append(hf._element)

    ilova_anchor = None
    for root in parts:
        for p_el in list(root.iter(qn("w:p"))):
            text = "".join(t.text or "" for t in _texts(p_el)).strip()
            m = re.fullmatch(r"\{\{\s*(matn|jadval):([\w\-]+)\s*\}\}", text)
            if m and m.group(1) == "matn":
                _expand_block(p_el, blocks.get(m.group(2), []))
            elif m:
                for i, t in enumerate(by_ilova.get(m.group(2), [])[: INLINE_TABLES.get(m.group(2), 99)]):
                    tbl = _build_table(doc, t["headers"], t["rows"], 9, PORTRAIT_CM)
                    p_el.addprevious(tbl._tbl)
                    p_el.addprevious(_new_paragraph(doc)._p)
                    del i
                p_el.getparent().remove(p_el)
            elif text == "{{ilovalar}}":
                ilova_anchor = p_el
            else:
                _replace_inline(p_el, values)

    if ilova_anchor is not None:
        # "8. Moliyaviy hisob-kitoblar" sarlavhasi ham albom bo'limiga o'tadi (kitob betida yolg'iz qolmasin)
        prev = ilova_anchor.getprevious()
        heading_el = prev if prev is not None and prev.tag == qn("w:p") and             "".join(t.text or "" for t in _texts(prev)).strip().startswith("8.") else ilova_anchor
        # oldingi bo'sh paragraflar va sahifa uzilishlari bo'sh bet qoldirmasin
        prev = heading_el.getprevious()
        while prev is not None and prev.tag == qn("w:p") and not "".join(t.text or "" for t in _texts(prev)).strip()                 and prev.find(qn("w:pPr") + "/" + qn("w:sectPr")) is None:
            nxt = prev.getprevious()
            prev.getparent().remove(prev)
            prev = nxt
        _landscape_from_here(doc, heading_el)
        last = None
        for t in tables:
            first_of_group = t.get("ilova") != last
            title = f"{t.get('ilova', '')}. {t.get('title', '')}" if first_of_group else t.get("title", "")
            head = _new_paragraph(doc, title, bold=True, size=11, center=True)
            head.paragraph_format.keep_with_next = True
            head.paragraph_format.space_before = Pt(10 if first_of_group else 4)
            ilova_anchor.addprevious(head._p)
            tbl = _build_table(doc, t["headers"], t["rows"], 7.5 if len(t["headers"]) > 8 else 9, LANDSCAPE_CM)
            ilova_anchor.addprevious(tbl._tbl)
            ilova_anchor.addprevious(_new_paragraph(doc)._p)
            last = t.get("ilova")
        ilova_anchor.getparent().remove(ilova_anchor)

    # title o'zgartirilmaydi: shablon muqovasi va headeri uni "BIZNES-REJA" sifatida ko'rsatadi
    doc.core_properties.subject = ctx.get("loyiha_nomi") or ""
    doc.core_properties.author = ctx.get("tashabbuskor") or ""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    doc.save(output_path)
    return output_path

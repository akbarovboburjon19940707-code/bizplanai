"""Word hujjati bank shabloni asosida (docs/WORD_SHABLON_TAHLILI.md)."""
import re
import zipfile

import pytest
from docx import Document

from app.engine.financial_engine import calculate_financial_model
from app.engine.word_generator import generate_word_report
from tests.test_template_model import EXCEL_INPUT

BASE = {k: v for k, v in EXCEL_INPUT.items() if k != "tannarx_ulushi"} | {
    "tashabbuskor": "Baraka MChJ", "fio": "Karimov Aziz", "manzil": "Samarqand viloyati, Urgut tumani",
    "bank": "Hamkorbank ATB", "stir": "123456789", "mulk": "MChJ",
}


def render(tmp_path, **over):
    model = calculate_financial_model({**BASE, **over})
    path = tmp_path / "reja.docx"
    generate_word_report(model, str(path))
    return model, path


def find_table(doc, first_cell_prefix: str):
    return next(t for t in doc.tables if t.cell(0, 0).text.strip().startswith(first_cell_prefix))


def all_xml_text(path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = "".join(z.read(n).decode("utf-8") for n in z.namelist()
                      if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n))
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))


@pytest.mark.parametrize("faoliyat", ["ishlab_chiqarish", "qishloq_xojaligi", "savdo", "xizmat"])
def test_no_placeholders_left_for_each_activity(tmp_path, faoliyat):
    _, path = render(tmp_path, faoliyat_turi=faoliyat)
    text = all_xml_text(path)
    assert "{{" not in text and "}}" not in text
    assert "Дата" not in text and "Hisobot sanasi:" in text
    assert "sanoat industriyasini" not in text and "rentabel1igini" not in text


def test_initiator_table_has_correct_credit_terms(tmp_path):
    _, path = render(tmp_path)
    doc = Document(str(path))
    rows = {r.cells[1].text.strip(): r.cells[2].text.strip() for r in doc.tables[1].rows[1:]}
    assert rows["Kredit foizi"] == "18 %"           # asl shablonda imtiyoz chiqardi
    assert rows["Imtiyozli davri"] == "24 oy"
    assert rows["Xizmat ko‘rsatuvchi bank:"] == "Hamkorbank ATB"
    assert re.fullmatch(r"100 000 000 so.m", rows["Kredit miqdori"])
    assert [r.cells[0].text for r in doc.tables[1].rows[1:4]] == ["1", "2", "3"]


def test_tables_inserted_and_appendices_landscape(tmp_path):
    model, path = render(tmp_path)
    doc = Document(str(path))
    # shablondagi 5 ta + 5 ta matn ichidagi + barcha ilovalar
    assert len(doc.tables) == 5 + 5 + len(model["tables"])
    assert len(doc.sections) == 2
    assert doc.sections[0].page_width < doc.sections[0].page_height
    assert doc.sections[1].page_width > doc.sections[1].page_height
    body = "\n".join(p.text for p in doc.paragraphs)
    for ilova in ("1-ILOVA. LOYIHA QIYMATI", "14-ILOVA. NPV, IRR, DPP, PI HISOBI"):
        assert ilova in body


def test_activity_specific_texts_and_swot(tmp_path):
    _, path = render(tmp_path, faoliyat_turi="savdo")
    doc = Document(str(path))
    body = "\n".join(p.text for p in doc.paragraphs)
    assert "Savdo do‘koni manzili: Samarqand viloyati, Urgut tumani." in body
    assert "Ushbu savdo loyihasi Baraka MChJ nomidan" in body
    swot = find_table(doc, "S – Kuchli")
    assert "Xaridorlar oqimi yuqori" in swot.cell(0, 0).text
    assert swot.cell(1, 2).text.strip() == "S > W"
    matrix = next(t for t in doc.tables if t.cell(0, 1).text.strip() == "Mazmuni")
    assert matrix.cell(2, 2).text.strip() == "70%"


def test_staff_text_from_input(tmp_path):
    _, path = render(tmp_path, direktor=1, xodim=4, yangi_xodim=2)
    body = "\n".join(p.text for p in Document(str(path)).paragraphs)
    assert "Korxonada jami 7 nafar xodim faoliyat ko‘rsatadi: 1 nafar rahbar va 6 nafar ishchi." in body
    assert "Shundan 2 nafari uchun loyiha doirasida yangi ish o‘rni tashkil etiladi." in body


def test_user_text_is_not_reinterpreted(tmp_path):
    _, path = render(tmp_path, tashabbuskor="{{kredit}} MChJ", loyiha_nomi="Non {{matn:xulosa}}")
    text = all_xml_text(path)
    assert "{{kredit}} MChJ" in text and "Non {{matn:xulosa}}" in text
    # qolgan barcha "{{" faqat foydalanuvchi matnidan
    assert text.count("{{") == text.count("{{kredit}} MChJ") + text.count("Non {{matn:xulosa}}")


def test_blank_fields_get_lines_and_ai_text_used(tmp_path):
    model = calculate_financial_model({**BASE, "stir": None, "fio": None})
    path = tmp_path / "ai.docx"
    generate_word_report(model, str(path), {"bozor_tahlili": {"title": "Bozor", "text": "AI bozor matni 1.\nAI bozor matni 2."}})
    doc = Document(str(path))
    body = [p.text for p in doc.paragraphs]
    assert "AI bozor matni 1." in body and "AI bozor matni 2." in body
    rows = {r.cells[1].text.strip(): r.cells[2].text.strip() for r in doc.tables[1].rows[1:]}
    assert rows["STIR:"].startswith("____")


def test_default_text_color_matches_body(tmp_path):
    """Jadvallardagi (rangi berilmagan) matn asosiy matn bilan bir xil qora bo'lishi kerak, kulrang emas."""
    _, path = render(tmp_path)
    with zipfile.ZipFile(path) as z:
        styles = z.read("word/styles.xml").decode()
    default = re.search(r"<w:rPrDefault>.*?</w:rPrDefault>", styles, re.S).group(0)
    assert '<w:color w:val="000000"/>' in default


def test_short_loan_term_documents_have_only_those_years(tmp_path):
    from openpyxl import load_workbook

    from app.engine.excel_generator import generate_excel_report

    model, path = render(tmp_path, muddat=36, imtiyoz=0)
    text = all_xml_text(path)
    assert "3-yil" in text and "4-yil" not in text and "10-yil" not in text
    xlsx = tmp_path / "reja.xlsx"
    generate_excel_report(model, str(xlsx))
    wb = load_workbook(xlsx)
    cells = {str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None}
    assert "3-yil" in cells and "4-yil" not in cells

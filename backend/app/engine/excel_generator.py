"""
UzBizness / BizplanAI — Professional Excel (.xlsx) Moliyaviy Model Generatori
10 yillik investitsiya va kredit hisob-kitoblari (O'zbekiston banklari standarti).
openpyxl kutubxonasi asosida yuqori unumdorlik va to'liq formatlangan eksport.
"""

import os
import math
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ── Ranglar va Uslublar Palitrasi ──
NAVY_HEADER_FILL = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
WHITE_BOLD_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

SECTION_HEADER_FILL = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
SECTION_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

TOTAL_ROW_FILL = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
TOTAL_FONT = Font(name="Calibri", size=11, bold=True, color="92400E")

TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="4B5563")
REGULAR_FONT = Font(name="Calibri", size=10, color="111827")
BOLD_FONT = Font(name="Calibri", size=10, bold=True, color="111827")

THIN_GRAY = Side(border_style="thin", color="D1D5DB")
CELL_BORDER = Border(left=THIN_GRAY, right=THIN_GRAY, top=THIN_GRAY, bottom=THIN_GRAY)
DOUBLE_BOTTOM = Border(left=THIN_GRAY, right=THIN_GRAY, top=THIN_GRAY, bottom=Side(border_style="double", color="1E3A8A"))

ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_HEADER = Alignment(horizontal="center", vertical="center", wrap_text=True)

NUM_FORMAT_CURRENCY = "#,##0"
NUM_FORMAT_PERCENT = "0.0%"
NUM_FORMAT_DECIMAL = "#,##0.00"


def _format_cell(cell, value, is_header=False, is_total=False, is_title=False):
    cell.border = CELL_BORDER
    if is_title:
        cell.font = TITLE_FONT
        cell.alignment = ALIGN_LEFT
        return

    if is_header:
        cell.fill = NAVY_HEADER_FILL
        cell.font = WHITE_BOLD_FONT
        cell.alignment = ALIGN_HEADER
        return

    if is_total:
        cell.fill = TOTAL_ROW_FILL
        cell.font = TOTAL_FONT
        cell.border = DOUBLE_BOTTOM

    if isinstance(value, (int, float)):
        cell.value = value
        cell.alignment = ALIGN_RIGHT
        if isinstance(value, float) and 0 < abs(value) < 1:
            cell.number_format = NUM_FORMAT_PERCENT
        else:
            cell.number_format = NUM_FORMAT_CURRENCY
    else:
        str_val = str(value) if value is not None else ""
        if str_val.endswith("%"):
            try:
                num = float(str_val.rstrip("%")) / 100.0
                cell.value = num
                cell.number_format = NUM_FORMAT_PERCENT
                cell.alignment = ALIGN_RIGHT
            except Exception:
                cell.value = str_val
                cell.alignment = ALIGN_LEFT
        else:
            cell.value = str_val
            cell.alignment = ALIGN_LEFT if not is_header else ALIGN_CENTER
            if not is_total:
                cell.font = REGULAR_FONT


def _adjust_column_widths(ws, min_width=12, max_width=45):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(min_width, min(max_len + 3, max_width))


def _build_monthly_loan_schedule(ws, context: dict):
    """Oyma-oy kredit to'lov jadvali (120 oygacha, annuitet yoki differentsial)."""
    kredit = float(context.get("kredit") or 0)
    foiz = float(context.get("foiz") or 14)
    muddat = int(context.get("muddat") or 120)
    imtiyoz = int(context.get("imtiyoz") or 0)
    kredit_turi = str(context.get("kredit_turi") or "annuitet").strip().lower()

    ws.title = "Kredit jadvali (Oylik)"
    ws.append(["KREDITNING OYMA-OY SO'NDIRISH JADVALI"])
    ws.cell(row=1, column=1).font = TITLE_FONT
    ws.append([
        f"Loyiha: {context.get('loyiha_nomi', '')} | Kredit: {kredit:,.0f} so'm | "
        f"Foiz: {foiz}% | Muddat: {muddat} oy | Imtiyoz: {imtiyoz} oy | Turi: {kredit_turi.title()}"
    ])
    ws.cell(row=2, column=1).font = SUBTITLE_FONT
    ws.append([])

    headers = [
        "Oy", "Yil", "Davr", "Boshlang'ich qoldiq",
        "Asosiy qarz to'lovi", "Foiz to'lovi", "Jami oylik to'lov", "Oxirgi qoldiq"
    ]
    ws.append(headers)
    hdr_row = 4
    for col_idx in range(1, len(headers) + 1):
        _format_cell(ws.cell(row=hdr_row, column=col_idx), headers[col_idx - 1], is_header=True)

    r_month = (foiz / 100.0) / 12.0
    asosiy_muddat = max(1, muddat - imtiyoz)
    qoldiq = kredit

    total_principal = 0.0
    total_interest = 0.0
    total_payment = 0.0

    current_row = hdr_row + 1
    for m in range(1, muddat + 1):
        year = (m - 1) // 12 + 1
        month_in_year = (m - 1) % 12 + 1
        bosh_qoldiq = qoldiq
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

        oxir_qoldiq = qoldiq
        total_principal += a_tolov
        total_interest += f_tolov
        total_payment += tolov

        row_vals = [
            m, f"{year}-yil", f"{month_in_year}-oy",
            round(bosh_qoldiq, 2), round(a_tolov, 2),
            round(f_tolov, 2), round(tolov, 2), round(oxir_qoldiq, 2)
        ]
        ws.append(row_vals)
        for c_idx, val in enumerate(row_vals, 1):
            _format_cell(ws.cell(row=current_row, column=c_idx), val)
        current_row += 1

    # Yig'indi qatori
    tot_vals = ["JAMI", "", "", "", round(total_principal, 2), round(total_interest, 2), round(total_payment, 2), 0]
    ws.append(tot_vals)
    for c_idx, val in enumerate(tot_vals, 1):
        _format_cell(ws.cell(row=current_row, column=c_idx), val, is_total=True)

    ws.freeze_panes = "D5"
    _adjust_column_widths(ws)


def generate_excel_report(model_data: dict, output_path: str) -> str:
    """
    model_data ichidagi barcha 10 yillik moliyaviy jadvallarni
    chiroyli formatlangan .xlsx fayliga eksport qiladi.
    """
    ctx = model_data.get("context", {})
    tables = model_data.get("tables", [])

    wb = Workbook()
    wb.remove(wb.active)  # Standart bo'sh varaqni o'chiramiz

    # Varaq nomlari moslamasi
    SHEET_NAMES = {
        "1-ILOVA": "1-Loyiha qiymati",
        "2-ILOVA": "2-Moliyalashtirish",
        "3-ILOVA": "3-Tashabbuskor hissasi",
        "4-ILOVA": "4-Amortizatsiya (10y)",
        "5-ILOVA": "5-Ish haqi fondi",
        "KOMMUNAL": "5-Foydalanish xarajatlari",
        "6-ILOVA": "6-Sotish rejasi (10y)",
        "7-ILOVA": "7-Soliqlar (10y)",
        "8-9-ILOVA": "8-9-Kredit grafigi",
        "10-ILOVA": "10-Zararsiz nuqta",
        "11-ILOVA": "11-Tannarx va xarajatlar",
        "12-ILOVA": "12-Foyda va zararlar",
        "13-ILOVA": "13-Pul oqimi (CashFlow)",
        "14-ILOVA": "14-NPV va Samaradorlik",
    }

    sheets = {}  # bir xil ilova jadvallari bitta varaqqa ketma-ket yoziladi

    for tbl in tables:
        ilova = tbl.get("ilova", "Jadval")
        ws = sheets.get(ilova)
        if ws is None:
            ws = wb.create_sheet(title=SHEET_NAMES.get(ilova, ilova[:31]))
            sheets[ilova] = ws
            ws.append([f"{tbl.get('ilova', '')}: {tbl.get('title', '')}"])
            ws.cell(row=1, column=1).font = TITLE_FONT
            ws.append([f"Loyiha: {ctx.get('loyiha_nomi', 'Biznes Reja')} | Tashabbuskor: {ctx.get('tashabbuskor', '')}"])
            ws.cell(row=2, column=1).font = SUBTITLE_FONT
            ws.append([])
            ws.freeze_panes = "B5"
        else:
            ws.append([])
            ws.append([tbl.get("title", "")])
            ws.cell(row=ws.max_row, column=1).font = TITLE_FONT

        # Headers
        headers = tbl.get("headers", [])
        ws.append(headers)
        hdr_row = ws.max_row
        for c_idx, h in enumerate(headers, 1):
            _format_cell(ws.cell(row=hdr_row, column=c_idx), h, is_header=True)

        # Rows
        for r in tbl.get("rows", []):
            ws.append(r)
            cur_row = ws.max_row
            first_cell_str = str(r[0] if r else "").upper()
            is_tot = any(w in first_cell_str for w in ["JAMI", "UMUMIY", "SOF FOYDA", "SOF PUL OQIMI", "YALPI JAMI", "SOF JORIY", "SOF HOZIRGI", "TANNARX"])
            for c_idx, val in enumerate(r, 1):
                _format_cell(ws.cell(row=cur_row, column=c_idx), val, is_total=is_tot)

    for ws in sheets.values():
        _adjust_column_widths(ws)

    # Alohida: Oylik to'liq kredit amortizatsiya jadvali
    loan_ws = wb.create_sheet(title="Kredit oylik jadval")
    _build_monthly_loan_schedule(loan_ws, ctx)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    return output_path

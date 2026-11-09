"""Asl Word shablonidan (eski sayt template.docx) tuzatilgan ish shablonini yasaydi.

    python scripts/build_word_template.py

Kirish:  app/engine/templates/source/template_original.docx (o'zgarmaydi)
Chiqish: app/engine/templates/biznes_reja.docx
Tahlil va qarorlar: docs/WORD_SHABLON_TAHLILI.md. Har bir o'zgartirish asl matnni tekshiradi:
shablon boshqacha bo'lsa skript xato beradi (jim buzilmaydi).

Belgilar (renderer: app/engine/word_template.py):
  {{kalit}}            oddiy qiymat (run'lar bo'lingan bo'lsa ham)
  {{matn:kalit}}       paragraf o'rniga bir yoki bir nechta paragraf (faoliyat turiga qarab)
  {{jadval:N-ILOVA}}   paragraf o'rniga moliyaviy jadval
  {{ilovalar}}         barcha ilovalar (albom varaqlarda)
"""
import copy
import os
import re
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE = os.path.join(os.path.dirname(__file__), "..", "app", "engine", "templates")
SRC = os.path.join(BASE, "source", "template_original.docx")
OUT = os.path.join(BASE, "biznes_reja.docx")

Q = "[‘’'`]"  # shablonda tutuq belgilari aralash


def norm(s: str) -> str:
    return re.sub(Q, "'", s).replace(" ", " ").strip()


def expect(p, pattern: str):
    if not re.search(pattern, norm(p.text), flags=re.I):
        sys.exit(f"Shablon kutilganidek emas: {pattern!r} topilmadi, bor: {p.text[:80]!r}")


def set_text(p, text: str):
    """Birinchi run formatini saqlab, paragraf matnini almashtiradi."""
    runs = p.runs
    if not runs:
        p.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    # run'dan tashqaridagi qoldiqlar (hyperlink, smartTag) ichidagi matnlarni ham tozalash
    for t in p._p.xpath("./*[not(self::w:r) and not(self::w:pPr)]//w:t"):
        t.text = ""


def insert_after(p, text: str, like=None):
    """p dan keyin yangi paragraf (like paragrafining uslubi va formati bilan)."""
    src = like if like is not None else p
    new = copy.deepcopy(src._p)
    p._p.addnext(new)
    from docx.text.paragraph import Paragraph
    para = Paragraph(new, p._parent)
    # sahifa uzilishi va rasmlar nusxalanmasin
    for el in new.xpath(".//w:br[@w:type='page'] | .//w:drawing"):
        el.getparent().remove(el)
    set_text(para, text)
    return para


def delete(p):
    p._p.getparent().remove(p._p)


def heading(p, text: str, style: str = "Heading 1"):
    p.style = p.part.document.styles[style]
    set_text(p, text)


def set_cell(cell, texts: list[str]):
    """Katak paragraflarini almashtiradi: birinchi paragraf formati saqlanadi."""
    paras = cell.paragraphs
    for p, t in zip(paras, texts, strict=False):  # ortiqcha paragraflar pastda o'chiriladi
        set_text(p, t)
    for p in paras[len(texts):]:
        delete(p)
    last = cell.paragraphs[-1]
    for t in texts[len(paras):]:
        last = insert_after(last, t)


def main():
    doc = Document(SRC)
    P = doc.paragraphs  # indekslar asl shablon bo'yicha; o'chirish oxirida qilinadi
    to_delete = []
    expect(P[84], r"^Mahalliy iqtisodiyotning hozirgi holatining")
    body_ref = P[84]  # oddiy matn paragrafi: AI va standart matnlar shu formatda chiqadi

    def as_body(p, key: str):
        """Placeholder paragrafi o'rniga oddiy matn formatidagi {{matn:key}} paragrafi."""
        insert_after(p, f"{{{{matn:{key}}}}}", like=body_ref)
        to_delete.append(p)

    # Muqova
    expect(P[4], r"2026 yil")
    set_text(P[4], "«____» ______________ {{yil}} yil")
    expect(P[10], r"\{\{business_image\}\}")
    set_text(P[10], "{{matn:rasm}}")

    # Memorandum
    expect(P[46], r"^O'zbekiston sanoat industriyasini rivojlantirish bo'yicha ushbu loyiha")
    set_text(P[46], re.sub(r"^O.zbekiston sanoat industriyasini rivojlantirish bo.yicha ushbu loyiha",
                           "Ushbu {{soha_nomi}} loyihasi", P[46].text))
    expect(P[56], r"2026 yil holatiga")
    set_text(P[56], "Barcha narxlar {{yil}} yil holatiga qabul qilingan.")

    # 1-bo'lim
    heading(P[60], "1.\tLoyiha tashabbuskori to‘g‘risida ma’lumot")
    tbl = doc.tables[1]
    rows = {norm(r.cells[1].text): r for r in tbl.rows[1:]}
    for i, r in enumerate(tbl.rows[1:], start=1):
        set_cell(r.cells[0], [str(i)])
    fixes = {
        "Xizmat ko'rsatuvchi bank:": "{{bank}}",
        "JSHSHIR:": "{{jshshir}}",
        "Pasport seriya raqami:": "{{pasport}}",
        "Berilgan vaqti:": "{{pasport_berilgan}}",
        "Loyihaning qiymati": "{{loyiha_qiymati}} so‘m",
        "Kredit foizi": "{{foiz}} %",       # asl shablonda {{imtiyoz}} edi
        "Imtiyozli davri": "{{imtiyoz}} oy",  # asl shablonda {{foiz}} edi
    }
    for label, value in fixes.items():
        if label not in rows:
            sys.exit(f"1-bo'lim jadvalida {label!r} qatori topilmadi")
        set_cell(rows[label].cells[2], [value])

    # 2-bo'lim
    heading(P[62], "2.\tLoyiha maqsadi va yo‘nalishi")
    expect(P[63], r"^Bugungi kunda Respublikamizda")
    set_text(P[63], "{{matn:maqsad}}")
    expect(P[64], r"mazkur loyixani amalga oshirishi")
    to_delete.append(P[64])
    expect(P[68], r"xom ashyo bazasi")
    set_text(P[68], "{{matn:resurs}}")
    expect(P[69], r"\{\{loyiha_maqsadi\}\}")
    set_text(P[69], "{{matn:talab}}")
    insert_after(P[69], "{{matn:loyiha_maqsadi}}", like=body_ref)
    expect(P[70], r"1-jadval\. Loyiha qiymati")
    set_text(P[70], "Maqsadlarga erishish uchun korxona kredit mablag‘larini jalb qilishga qaror qildi.")
    cap = insert_after(P[70], "1-jadval. Loyiha qiymati", like=P[148])
    insert_after(cap, "{{jadval:1-ILOVA}}", like=P[147])

    # 3-bo'lim
    heading(P[71], "3.\tBozor kon’yunkturasi tahlili")
    expect(P[74], r"ishlab chiqaruvchi tadbirkorlar kamligi")
    set_text(P[74], "{{matn:raqobat}}")
    expect(P[75], r"tumanga kirib kelayotgan")
    to_delete.append(P[75])
    expect(P[82], r"\{\{bozor_tahlili\}\}")
    as_body(P[82], "bozor_tahlili")
    expect(P[91], r"maksimal darajada aylantiring")
    set_text(P[91], "ko‘rsatiladigan mahsulot va xizmatlar doirasini kengaytirish;")
    expect(P[93], r"rentabel1igini")
    set_text(P[93], "Bularning barchasi korxona rentabelligini oshirishga yordam berishi kerak.")
    expect(P[94], r"barqaror va barqaror")
    set_text(P[94], "Rejalashtirilgan mahsulot va xizmatlar mahalliy bozorda barqaror talabga ega bo‘lib, "
                    "kelgusida asosiy e’tibor mahalliy bozorga qaratiladi.")
    expect(P[95], r"sifatli mahsulotlar taqdim etishdir")
    set_text(P[95], "Korxonaning asosiy maqsadi mijozlarga sifatli mahsulot va xizmatlar taqdim etishdir.")
    expect(P[96], r"swot tahlili")
    heading(P[96], "3.2.\tLoyihaning SWOT tahlili", "Heading 2")
    expect(P[99], r"\{\{marketing_rejasi\}\}")
    as_body(P[99], "marketing_rejasi")
    expect(P[103], r"\{\{risk_tahlili\}\}")
    as_body(P[103], "risk_tahlili")
    expect(P[106], r"Loyihaning_swot_tahlili")
    set_text(P[106], "Loyihaning SWOT tahlili")
    expect(P[108], r"\{\{swot_tahlili\}\}")
    as_body(P[108], "swot_tahlili")

    # 4P jadvali (2-jadval)
    t4p = doc.tables[2]
    set_cell(t4p.cell(0, 0), ["    Product – Mahsulot (xizmat)", "{{p4_product}}"])
    set_cell(t4p.cell(0, 1), ["    Price – Narx", "{{p4_price}}"])
    set_cell(t4p.cell(1, 0), ["    Place – Joy", "{{p4_place}}"])
    set_cell(t4p.cell(1, 1), ["    Promotion – Targ‘ibot", "{{p4_promotion}}"])

    # Marketing matritsasi (3-jadval)
    tm = doc.tables[3]
    for s in (1, 2, 3):
        set_cell(tm.cell(0, s + 1), [f"Segment {s}", f"({{{{seg{s}_nomi}}}})"])
        for row, key in ((1, "tavsif"), (2, "ulush"), (3, "geo"), (4, "talab"), (5, "xarid"), (6, "jalb")):
            set_cell(tm.cell(row, s + 1), [f"{{{{seg{s}_{key}}}}}"])
    set_cell(tm.cell(4, 1), ["Talabning kamayishi, ko‘payishi yoki barqarorligi"])
    set_cell(tm.cell(5, 1), ["Xarid qobiliyati"])
    set_cell(tm.cell(6, 1), ["Iste’molchilarni jalb etish"])
    set_cell(tm.cell(0, 0), ["№"])

    # SWOT matritsasi (4-jadval)
    ts = doc.tables[4]
    set_cell(ts.cell(0, 0), ["S – Kuchli tomonlar:", "{{matn:swot_s}}"])
    set_cell(ts.cell(0, 1), ["W – Kuchsiz tomonlar:", "{{matn:swot_w}}"])
    set_cell(ts.cell(4, 0), ["O – Imkoniyatlar:", "{{matn:swot_o}}"])
    set_cell(ts.cell(4, 1), ["T – Tahdidlar:", "{{matn:swot_t}}"])
    for r in range(8):
        set_cell(ts.cell(r, 2), [f"{{{{matn:swot_c{r}}}}}"])

    # 4-5 bo'limlar
    heading(P[109], "4.\tArxitektura-qurilish va texnik-texnologik talablar")
    expect(P[111], r"Ishlab chiqarish binosi manzili")
    set_text(P[111], "{{bino_turi}} manzili: {{manzil}}.")
    expect(P[121], r"\{\{texnik_tahlil\}\}")
    as_body(P[121], "texnik_tahlil")
    heading(P[122], "5.\tEkologik aspekt")
    expect(P[124], r"ishlab chiqarish\(xizmat")
    set_text(P[124], "{{matn:ekologiya}}")
    expect(P[125], r"Ishlab chiqarish davomida")
    set_text(P[125], "Faoliyat jarayonida atrof-muhitga zarar yetkazuvchi kimyoviy moddalar yoki xavfli chiqindilar "
                     "hosil bo‘lishi ko‘zda tutilmagan. Yuzaga keladigan chiqindilar asosan maishiy qoldiqlardan "
                     "iborat bo‘lib, ular belgilangan tartibda yig‘ilib, maxsus chiqindi yig‘ish joylariga topshiriladi.")

    # 6-bo'lim
    heading(P[128], "6.\tMoliya-xo‘jalik rejasi")
    expect(P[131], r"asosiy shtatda 1 ta xodim")
    set_text(P[131], "{{matn:shtat}}")
    expect(P[132], r"\{\{fio\}\}hisoblanadi")
    set_text(P[132], "Korxonani boshqarish va kerakli qarorlarni qabul qilish huquqi biriktirilgan asosiy mansabdor "
                     "shaxs – rahbar {{fio}} hisoblanadi.")
    set_text(P[137], "Mahsulot va xizmatlarni tatbiq etish;")
    set_text(P[138], "Yangi bozorlarni o‘zlashtirish, faoliyat ko‘lamini oshirib borish;")
    expect(P[142], r"5-jadval")
    insert_after(P[142], "{{jadval:5-ILOVA}}", like=P[147])
    expect(P[148], r"6-jadval")
    insert_after(P[148], "{{jadval:6-ILOVA}}", like=P[147])
    expect(P[155], r"7-jadval")
    expect(P[156], r"\{\{business_image\}\}")  # asl shablonda jadval o'rnida rasm turgan
    set_text(P[156], "{{jadval:10-ILOVA}}")
    P[156].style = P[147].style
    expect(P[159], r"ishlab chiqarish faoliyatida")
    set_text(P[159], "Ma’lumki, har bir tadbirkorlik faoliyatida kommunikatsiya tizimlariga ehtiyoj seziladi. "
                     "Bugungi kunda zamonaviy texnologiyalardan foydalanishda bu tizimlarga talab yanada ortib bormoqda.")
    expect(P[161], r"8-jadval")
    insert_after(P[161], "{{jadval:KOMMUNAL}}", like=P[147])

    # 7-8 bo'limlar
    heading(P[162], "7.\tXulosa")
    set_text(P[164], "Ushbu biznes-reja yakuniy hujjat sifatida maxfiy ma’lumot hisoblanadi. Hujjat faqat tashabbuskor "
                     "tomonidan taqdim etilgan ma’lumotlar asosida tayyorlangan.")
    expect(P[173], r"\{\{xulosa\}\}")
    as_body(P[173], "xulosa")
    heading(P[183], "8.\tMoliyaviy hisob-kitoblar (ilovalar)")
    insert_after(P[183], "{{ilovalar}}", like=P[147])
    expect(P[187], r"\{\{extra_doc\}\}")
    to_delete += [P[185], P[187]]

    # jadval sarlavhalari o'z jadvalidan ajralib, bet oxirida qolmasin
    for p in doc.paragraphs:
        if re.match(r"^\s*(\d-jadval|MARKETING MATRISASI|Marketing majmui|Loyihaning SWOT tahlili)", p.text):
            p.paragraph_format.keep_with_next = True

    for p in to_delete:
        delete(p)

    # Footer: ruscha "Дата отчета" (sana content control) o'rniga hisobot sanasi
    for part in {id(s.footer.part): s.footer for s in doc.sections}.values(), \
            {id(s.first_page_footer.part): s.first_page_footer for s in doc.sections}.values():
        for footer in part:
            for sdt in footer._element.xpath(".//w:sdt"):
                if not re.search("[А-Яа-я]", "".join(sdt.itertext())):
                    continue
                r = OxmlElement("w:r")
                rpr = sdt.find(".//" + qn("w:rPr"))
                if rpr is not None:
                    r.append(copy.deepcopy(rpr))
                t = OxmlElement("w:t")
                t.set(qn("xml:space"), "preserve")
                t.text = "Hisobot sanasi: {{sana}}"
                r.append(t)
                sdt.addprevious(r)
                sdt.getparent().remove(sdt)

    doc.core_properties.title = "BIZNES-REJA"  # muqova va headerdagi sarlavha shu xususiyatdan olinadi
    doc.save(OUT)
    leftovers = sorted({m for p in Document(OUT).paragraphs for m in re.findall(r"\{\{[^}]+\}\}", p.text)})
    print(f"Saqlandi: {os.path.normpath(OUT)}\nBelgilar: {', '.join(leftovers)}")


if __name__ == "__main__":
    main()

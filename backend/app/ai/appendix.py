"""AI bo'limlarini tayyor Word hujjatiga alohida bob sifatida qo'shish (moliyaviy yadro o'zgarmaydi)."""
from docx import Document
from docx.enum.text import WD_BREAK


def append_ai_chapter(docx_path: str, sections: dict[str, dict]) -> None:
    if not sections:
        return
    doc = Document(docx_path)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.add_heading("Qo'shimcha tahlil", level=1)
    for item in sections.values():
        doc.add_heading(item["title"], level=2)
        for para in [p.strip() for p in item["text"].split("\n") if p.strip()]:
            doc.add_paragraph(para)
    doc.save(docx_path)

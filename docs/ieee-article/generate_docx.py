#!/usr/bin/env python3
"""Генерация .docx статьи PIERE 2026 из Markdown по шаблону IEEE.

Читает `draft-article-en.md`, создаёт `PIERE2026_Papin_generated.docx`:
заголовок/авторы/аннотация — в одну колонку, тело — в две колонки,
Times New Roman, таблицы, рисунки, подписи.

Зависимости: python-docx (pip install python-docx).

Запуск:
    python3 docs/ieee-article/generate_docx.py
"""

import os
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "draft-article-en.md")
OUT = os.path.join(HERE, "PIERE2026_Papin_generated.docx")

ALIGN = {
    "just": WD_ALIGN_PARAGRAPH.JUSTIFY,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "left": WD_ALIGN_PARAGRAPH.LEFT,
}


def set_cols(section, num):
    """Число колонок в секции."""
    cols = section._sectPr.xpath("./w:cols")
    if cols:
        cols[0].set(qn("w:num"), str(num))


def add(doc, text, size=10, bold=False, italic=False, align="just", sb=0, sa=0):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    p.alignment = ALIGN[align]
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after = Pt(sa)
    return p


def main():
    lines = open(SRC, encoding="utf-8").read().splitlines()
    doc = Document()
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Cm(1.78)
    sec.top_margin = sec.bottom_margin = Cm(1.9)

    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(10)
    st._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    st.paragraph_format.space_after = Pt(0)
    st.paragraph_format.line_spacing = 1.0

    i = 0
    body_started = False
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Таблица
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[-: ]+$", "".join(cells)):
                    rows.append(cells)
                i += 1
            if rows:
                t = doc.add_table(rows=len(rows), cols=len(rows[0]))
                t.style = "Table Grid"
                for ri, row in enumerate(rows):
                    for ci, c in enumerate(row[: len(rows[0])]):
                        pr = t.cell(ri, ci).paragraphs[0]
                        rr = pr.add_run(c)
                        rr.font.size = Pt(8)
                        rr.font.name = "Times New Roman"
                        rr.bold = ri == 0
            continue

        # Рисунок
        m = re.match(r"!\[.*?\]\((.+?)\)", line)
        if m:
            try:
                doc.add_picture(m.group(1), width=Cm(7.5))
            except Exception:
                add(doc, f"[image: {m.group(1)}]")
            i += 1
            continue

        if line.startswith("# "):
            add(doc, line[2:], size=24, align="center", sa=6)
        elif line.startswith("## "):
            if not body_started:
                new = doc.add_section(WD_SECTION.CONTINUOUS)
                set_cols(new, 2)
                new.left_margin = new.right_margin = Cm(1.78)
                body_started = True
            add(doc, line[3:], size=10, bold=True, align="center", sb=6, sa=2)
        elif line.startswith("### "):
            add(doc, line[4:], size=10, italic=True, align="left", sb=4, sa=1)
        elif line.startswith("**Fig."):
            add(doc, re.sub(r"\*\*", "", line), size=8, align="center")
        elif line.startswith("**") and line.endswith("**"):
            add(doc, re.sub(r"\*\*", "", line), size=10, bold=True, align="left")
        elif line.startswith("---"):
            pass
        else:
            txt = re.sub(r"!\[.*?\]\(.*?\)", "", line)
            txt = re.sub(r"\*\*(.+?)\*\*", r"\1", txt)
            if txt.strip():
                add(doc, txt)
        i += 1

    doc.save(OUT)
    print(f"saved: {OUT}")


if __name__ == "__main__":
    main()

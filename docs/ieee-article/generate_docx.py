#!/usr/bin/env python3
"""Генерация .docx статьи PIERE 2026 из Markdown по шаблону IEEE.

Читает `draft-article-en.md`, создаёт `PIERE2026_Papin_generated.docx`:
заголовок/авторы/аннотация — в одну колонку, тело — в две колонки,
Times New Roman, таблицы, рисунки, подписи. Формулы LaTeX ($...$ и
$$...$$) конвертируются в нативные формулы Word (OMML).

Зависимости: python-docx, latex2mathml, mathml2omml.
    pip install python-docx latex2mathml mathml2omml

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
from lxml import etree

import latex2mathml.converter as l2m
import mathml2omml

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "draft-article-en.md")
OUT = os.path.join(HERE, "PIERE2026_Papin_generated.docx")
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

ALIGN = {
    "just": WD_ALIGN_PARAGRAPH.JUSTIFY,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "left": WD_ALIGN_PARAGRAPH.LEFT,
}


def set_cols(section, num):
    cols = section._sectPr.xpath("./w:cols")
    if cols:
        cols[0].set(qn("w:num"), str(num))


def latex_to_omml(latex):
    """LaTeX -> элемент OMML (для вставки в документ Word)."""
    ml = l2m.convert(latex)
    omml = mathml2omml.convert(ml)
    if "xmlns:m" not in omml:
        omml = omml.replace("<m:oMath>", f'<m:oMath xmlns:m="{M_NS}">', 1)
    return etree.fromstring(omml.encode())


def _style_run(r, size):
    r.font.name = "Times New Roman"
    r.font.size = Pt(size)
    return r


def add_para(doc, segments, size=10, bold=False, italic=False, align="just",
             sb=0, sa=0):
    """Абзац из сегментов: (text, None) или (None, latex)."""
    p = doc.add_paragraph()
    p.alignment = ALIGN[align]
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after = Pt(sa)
    for text, latex in segments:
        if latex is not None:
            try:
                p._p.append(latex_to_omml(latex))
            except Exception:
                _style_run(p.add_run(f" {latex} "), size)
        elif text:
            r = _style_run(p.add_run(text), size)
            r.bold = bold
            r.italic = italic
    return p


def split_math(text):
    """Разбить строку на сегменты (text | inline math)."""
    segs = []
    pos = 0
    for m in re.finditer(r"\$(.+?)\$", text):
        if m.start() > pos:
            segs.append((text[pos:m.start()], None))
        segs.append((None, m.group(1)))
        pos = m.end()
    if pos < len(text):
        segs.append((text[pos:], None))
    return segs or [(text, None)]


def flush(doc, buf):
    if not buf:
        return
    text = " ".join(buf)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    if text.strip():
        add_para(doc, split_math(text.strip()))
    buf.clear()


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

    buf = []
    body_started = False
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Display-формула $$...$$
        if line.startswith("$$"):
            flush(doc, buf)
            expr = line.strip("$").strip()
            expr = re.sub(r"\\tag\{.*?\}", "", expr).strip()
            add_para(doc, [(None, expr)], align="center", sb=4, sa=4)
            i += 1
            continue

        # Таблица
        if line.startswith("|"):
            flush(doc, buf)
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
                        rr = _style_run(pr.add_run(c), 8)
                        rr.bold = ri == 0
            continue

        # Рисунок
        m = re.match(r"!\[.*?\]\((.+?)\)", line)
        if m:
            flush(doc, buf)
            path = m.group(1)
            if not os.path.isabs(path):
                path = os.path.join(HERE, path)
            try:
                doc.add_picture(path, width=Cm(7.5))
            except Exception as e:
                add_para(doc, [(f"[image: {m.group(1)}] ({e})", None)])
            i += 1
            continue

        if line.startswith("# "):
            flush(doc, buf)
            add_para(doc, [(line[2:], None)], size=24, align="center", sa=6)
        elif line.startswith("## "):
            flush(doc, buf)
            if not body_started:
                new = doc.add_section(WD_SECTION.CONTINUOUS)
                set_cols(new, 2)
                new.left_margin = new.right_margin = Cm(1.78)
                body_started = True
            add_para(doc, [(line[3:], None)], size=10, bold=True,
                     align="center", sb=6, sa=2)
        elif line.startswith("### "):
            flush(doc, buf)
            add_para(doc, [(line[4:], None)], size=10, italic=True,
                     align="left", sb=4, sa=1)
        elif line.startswith("**Fig."):
            flush(doc, buf)
            add_para(doc, [(re.sub(r"\*\*", "", line), None)], size=8,
                     align="center")
        elif line.startswith("---"):
            flush(doc, buf)
        elif not line:
            flush(doc, buf)
        else:
            buf.append(line)
        i += 1
    flush(doc, buf)

    doc.save(OUT)
    print(f"saved: {OUT}")


if __name__ == "__main__":
    main()

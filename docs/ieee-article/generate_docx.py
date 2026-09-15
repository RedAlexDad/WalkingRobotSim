#!/usr/bin/env python3
"""Генерация .docx статьи PIERE 2026 из Markdown по шаблону PIERE.

Использует сам шаблон `PIERE2026_full_paper_template.docx` как основу,
поэтому применяются его стили: papertitle, Author, Affiliation, Abstract,
Keywords, heading 1 (style '1'), heading 2 (style '2'), Body Text ('a3'),
bulletlist, equation, figurecaption, references, tablehead/tablecopy.

Формулы LaTeX ($...$ и $$...$$) конвертируются в нативные уравнения Word
(OMML) через latex2mathml + mathml2omml.

Зависимости: python-docx, latex2mathml, mathml2omml.
Запуск: python3 docs/ieee-article/generate_docx.py
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
TEMPLATE = os.path.join(HERE, "PIERE2026_full_paper_template.docx")
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def latex_to_omml(latex):
    ml = l2m.convert(latex)
    omml = mathml2omml.convert(ml)
    if "xmlns:m" not in omml:
        omml = omml.replace("<m:oMath>", f'<m:oMath xmlns:m="{M_NS}">', 1)
    return etree.fromstring(omml.encode())


def _borders(table):
    """Границы таблицы (если в шаблоне нет стиля Table Grid)."""
    tblPr = table._tbl.tblPr
    borders = etree.SubElement(tblPr, qn("w:tblBorders"))
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = etree.SubElement(borders, qn(f"w:{edge}"))
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "000000")


def set_cols(section, num):
    cols = section._sectPr.xpath("./w:cols")
    if cols:
        cols[0].set(qn("w:num"), str(num))


def add(doc, segments, style=None, size=None, bold=False, italic=False,
        align=None, sb=None, sa=None):
    """Абзац (стиль шаблона) из сегментов (text|latex)."""
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    if sb is not None:
        p.paragraph_format.space_before = Pt(sb)
    if sa is not None:
        p.paragraph_format.space_after = Pt(sa)
    if isinstance(segments, str):
        segments = [(segments, None)]
    for text, latex in segments:
        if latex is not None:
            try:
                p._p.append(latex_to_omml(latex))
            except Exception:
                r = p.add_run(f" {latex} ")
                if size:
                    r.font.size = Pt(size)
        elif text:
            r = p.add_run(text)
            if size:
                r.font.size = Pt(size)
            r.bold = bold
            r.italic = italic
    return p


def split_math(text):
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


def main():
    doc = Document(TEMPLATE)
    # очистить содержимое, сохранив стили и sectPr
    body = doc.element.body
    for el in list(body):
        if el.tag in (qn("w:p"), qn("w:tbl")):
            body.remove(el)

    lines = open(SRC, encoding="utf-8").read().splitlines()
    buf = []
    body_started = False

    def flush():
        nonlocal buf
        if not buf:
            return
        text = " ".join(buf)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        if text.strip():
            style = "a3" if body_started else "Author"
            add(doc, split_math(text.strip()), style=style)
        buf = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("$$"):
            flush()
            expr = re.sub(r"\\tag\{.*?\}", "", line.strip("$").strip()).strip()
            add(doc, [(None, expr)], style="equation",
                align=WD_ALIGN_PARAGRAPH.CENTER)
            i += 1
            continue

        if line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[-: ]+$", "".join(cells)):
                    rows.append(cells)
                i += 1
            if rows:
                t = doc.add_table(rows=len(rows), cols=len(rows[0]))
                try:
                    t.style = "Table Grid"
                except KeyError:
                    _borders(t)
                for ri, row in enumerate(rows):
                    for ci, c in enumerate(row[: len(rows[0])]):
                        pr = t.cell(ri, ci).paragraphs[0]
                        rr = pr.add_run(c)
                        rr.font.size = Pt(8)
                        rr.font.name = "Times New Roman"
                        rr.bold = ri == 0
            continue

        m = re.match(r"!\[.*?\]\((.+?)\)", line)
        if m:
            flush()
            path = m.group(1)
            if not os.path.isabs(path):
                path = os.path.join(HERE, path)
            try:
                doc.add_picture(path, width=Cm(7.5))
            except Exception as e:
                add(doc, f"[image: {m.group(1)}] ({e})", style="a3")
            i += 1
            continue

        if line.startswith("# "):
            flush()
            add(doc, line[2:], style="papertitle")
        elif line.startswith("## Abstract"):
            flush()
            # собрать текст аннотации до следующего заголовка
            i += 1
            abuf = []
            while i < len(lines) and not lines[i].strip().startswith("**Keywords"):
                if lines[i].strip():
                    abuf.append(lines[i].strip())
                i += 1
            text = " ".join(abuf)
            add(doc, [("Abstract—", None)] + split_math(text), style="Abstract")
            continue
        elif line.startswith("## "):
            flush()
            if not body_started:
                new = doc.add_section(WD_SECTION.CONTINUOUS)
                set_cols(new, 2)
                body_started = True
            add(doc, line[3:], style="1")
        elif line.startswith("### "):
            flush()
            add(doc, line[4:], style="2")
        elif line.startswith("**Fig."):
            flush()
            add(doc, re.sub(r"\*\*", "", line), style="figurecaption")
        elif line.startswith("---"):
            flush()
        elif not line:
            flush()
        elif line.startswith("**Keywords**"):
            flush()
            rest = re.sub(r"\*\*Keywords\*\*\s*—?\s*", "", line)
            i += 1
            kbuf = [rest]
            while i < len(lines) and not lines[i].strip().startswith("##") and lines[i].strip():
                kbuf.append(lines[i].strip())
                i += 1
            add(doc, [("Keywords—", None)] + split_math(" ".join(kbuf)),
                style="Keywords")
            continue
        else:
            buf.append(line)
        i += 1
    flush()

    doc.save(OUT)
    print(f"saved: {OUT}")


if __name__ == "__main__":
    main()

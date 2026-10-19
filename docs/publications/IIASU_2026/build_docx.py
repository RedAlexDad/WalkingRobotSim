"""Сборка article.docx по шаблону ИИАСУ.

Требуется pandoc 3.12.1 (или совместимый) и python-docx.
Использование:
  .venv-lyrical/bin/python docs/publications/IIASU_2026/build_docx.py
"""
import os
import shutil
import subprocess
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

BASE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(BASE, "article.md")
RAW = "/tmp/opencode/article_raw.docx"
OUT = os.path.join(BASE, "article.docx")
PANDOC = os.environ.get("PANDOC") or shutil.which("pandoc") or "/tmp/opencode/pandoc/bin/pandoc"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def run_pandoc():
    cmd = [
        PANDOC, MD, "-o", RAW,
        "--from", "markdown+tex_math_dollars-implicit_figures",
        f"--resource-path={BASE}",
    ]
    subprocess.run(cmd, check=True)
    if not os.path.exists(RAW):
        raise SystemExit("pandoc не создал docx")


def set_font(run, size=12, bold=None):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), "Times New Roman")


def fmt(p, size=12, bold=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        first=0.0, before=0.0, after=0.0, line=1.5):
    p.alignment = align
    pf = p.paragraph_format
    pf.first_line_indent = Cm(first)
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    for r in p.runs:
        set_font(r, size, bold)


def set_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)


def number_equation(p, num):
    omp = p._p.find(f"{M}oMathPara")
    if omp is None:
        return
    omath = omp.find(f"{M}oMath")
    if omath is None:
        return
    p._p.remove(omp)
    pPr = p._p.get_or_add_pPr()
    old = pPr.find(qn("w:tabs"))
    if old is not None:
        pPr.remove(old)
    tabs = OxmlElement("w:tabs")
    for val, pos in (("center", Cm(8.75).twips), ("right", Cm(17.5).twips)):
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), val)
        tab.set(qn("w:pos"), str(int(pos)))
        tabs.append(tab)
    pPr.append(tabs)

    tab_run = OxmlElement("w:r")
    tab_run.append(OxmlElement("w:tab"))
    num_run = OxmlElement("w:r")
    num_run.append(OxmlElement("w:tab"))
    text = OxmlElement("w:t")
    text.text = f"({num})"
    num_run.append(text)

    p._p.append(tab_run)
    p._p.append(omath)
    p._p.append(num_run)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.line_spacing = 1.5
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)


def main():
    run_pandoc()
    doc = Document(RAW)

    # страница и поля — как в proceedings_template.docx
    s = doc.sections[0]
    s.page_width = Cm(21.0)
    s.page_height = Cm(29.7)
    s.left_margin = Cm(2.25)
    s.right_margin = Cm(1.25)
    s.top_margin = Cm(2.0)
    s.bottom_margin = Cm(2.0)

    for name in ("Normal", "Body Text", "First Paragraph"):
        try:
            st = doc.styles[name]
            st.font.name = "Times New Roman"
            st.font.size = Pt(12)
        except KeyError:
            pass

    title = next(p for p in doc.paragraphs
                 if p.text.strip().startswith("Обоснование выбора"))
    title.style = doc.styles["Normal"]
    fmt(title, 12, True, WD_ALIGN_PARAGRAPH.LEFT, 0, 12, 18)

    refs = False
    prev_table_caption = False
    math_idx = 0
    for p in doc.paragraphs:
        text = p.text.strip()
        if text.startswith("УДК"):
            fmt(p, 12, False, WD_ALIGN_PARAGRAPH.LEFT, 0, 0, 12)
        elif p._p is title._p:
            continue
        elif text.startswith(("Папин Алексей", "Канев Антон",
                              "Papin Alexey", "Kanev Anton")):
            fmt(p, 12, True, WD_ALIGN_PARAGRAPH.LEFT, 0, 0, 0)
        elif text.startswith("SPIN-код") or text.startswith("¹ "):
            fmt(p, 12, None, WD_ALIGN_PARAGRAPH.LEFT, 0, 0, 6)
        elif text.startswith("Аннотация."):
            fmt(p, 12, None, WD_ALIGN_PARAGRAPH.JUSTIFY, 0, 12, 12)
        elif text.startswith("Ключевые слова:"):
            fmt(p, 12, None, WD_ALIGN_PARAGRAPH.JUSTIFY, 0, 0, 12)
        elif text.startswith("Justification of the Choice"):
            p.style = doc.styles["Normal"]
            fmt(p, 12, True, WD_ALIGN_PARAGRAPH.LEFT, 0, 12, 18)
        elif text.startswith("Abstract."):
            fmt(p, 12, None, WD_ALIGN_PARAGRAPH.JUSTIFY, 0, 12, 12)
        elif text.startswith("Keywords:"):
            fmt(p, 12, None, WD_ALIGN_PARAGRAPH.JUSTIFY, 0, 0, 12)
        elif text.startswith("Таблица "):
            fmt(p, 11, None, WD_ALIGN_PARAGRAPH.LEFT, 0, 6, 0, 1.0)
            prev_table_caption = True
        elif prev_table_caption:
            fmt(p, 11, True, WD_ALIGN_PARAGRAPH.LEFT, 0, 0, 3, 1.0)
            prev_table_caption = False
        elif text.startswith("Рис. 1."):
            fmt(p, 8, False, WD_ALIGN_PARAGRAPH.CENTER, 0, 3, 12, 1.0)
        elif text.startswith("Список источников"):
            fmt(p, 12, True, WD_ALIGN_PARAGRAPH.LEFT, 0, 12, 6)
            refs = True
        elif p._p.findall(f".//{M}oMathPara"):
            math_idx += 1
            if math_idx in (2, 4):
                number_equation(p, 1 if math_idx == 2 else 2)
            else:
                fmt(p, 12, None, WD_ALIGN_PARAGRAPH.CENTER, 0, 6, 6)
        elif p._p.findall(f".//{W}drawing"):
            fmt(p, 12, None, WD_ALIGN_PARAGRAPH.CENTER, 0, 6, 3)
        elif refs:
            fmt(p, 12, None, WD_ALIGN_PARAGRAPH.JUSTIFY, 0, 0, 0)
            p.paragraph_format.left_indent = Cm(0.5)
            p.paragraph_format.first_line_indent = Cm(-0.5)
        else:
            first_run = p.runs[0] if p.runs else None
            heading = bool(first_run and first_run.bold and text.startswith(
                ("Введение.", "Материалы и методы.", "Результаты.",
                 "Обсуждение.", "Заключение.")))
            fmt(p, 12, None, WD_ALIGN_PARAGRAPH.JUSTIFY, 0 if heading else 1.0)

    # рисунок: 9 см по ширине, пропорционально
    for shape in doc.inline_shapes:
        shape.width = Cm(16.0)
        shape.height = Cm(16.0 * 3.2 / 7.16)

    # таблицы
    for table in doc.tables:
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True
        set_borders(table)
        for ri, row in enumerate(table.rows):
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_before = Pt(1)
                    p.paragraph_format.space_after = Pt(1)
                    for r in p.runs:
                        set_font(r, 10, True if ri == 0 else None)

    doc.core_properties.title = title.text
    doc.core_properties.author = "Папин А.В., Канев А.И."
    doc.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()

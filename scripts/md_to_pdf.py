#!/usr/bin/env python3
"""Convert Markdown to PDF: mermaid + KaTeX rendered in headless Chrome.

Usage:
    uv run --python 3.12 --with markdown python3 scripts/md_to_pdf.py FILE.md

Produces FILE.html and FILE.pdf next to the input (or in --out-dir).
Math ($...$, $$...$$) is passed through to KaTeX; ```mermaid blocks become
<div class="mermaid"> and are rendered by mermaid.js.
"""

from __future__ import annotations

import argparse
import html
import pathlib
import re
import shutil
import subprocess
import sys

import markdown

CSS = """
@page { size: A4 portrait; margin: 12mm; }
body { font-family: "PT Serif", Georgia, "Times New Roman", serif;
       font-size: 10pt; line-height: 1.24; color: #1a1a1a;
       max-width: 186mm; margin: 0 auto; }
h1 { font-size: 15pt; color: #14395c; border-bottom: 2px solid #2c5f8a;
     padding-bottom: 3px; }
h2 { font-size: 12pt; color: #14395c; border-bottom: 1px solid #cfd8e3;
     padding-bottom: 2px; margin: 10px 0 4px; }
h3 { font-size: 10.5pt; color: #2c5f8a; margin: 7px 0 3px; }
table { border-collapse: collapse; width: 100%; font-size: 8.6pt; margin: 5px 0; }
th, td { border: 1px solid #b9c4d0; padding: 2px 5px; text-align: left;
         vertical-align: top; }
th { background: #e8eef5; }
tr:nth-child(even) td { background: #f6f9fc; }
code { background: #eef1f4; padding: 0 3px; border-radius: 3px;
       font-family: Consolas, monospace; }
blockquote { border-left: 3px solid #2c5f8a; margin: 5px 0; padding: 2px 9px;
             background: #f6f9fc; }
.mermaid { text-align: center; margin: 6px 0; page-break-inside: avoid; }
.mermaid svg { max-width: 78%; height: auto; }
h2, h3 { page-break-after: avoid; }
table, tr, li { page-break-inside: avoid; }
.katex-display { margin: 4px 0; }
hr { border: none; border-top: 1px solid #cfd8e3; margin: 6px 0; }
"""

JS = """<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true, theme: "neutral" });</script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function () {
  renderMathInElement(document.body, {
    delimiters: [ { left: "$$", right: "$$", display: true },
                  { left: "$", right: "$", display: false } ],
    throwOnError: false });
});
</script>"""

HEAD = (
    "<!DOCTYPE html><html lang=\"ru\"><head><meta charset=\"utf-8\">"
    "<title>__TITLE__</title><style>" + CSS + "</style>" + JS
    + "</head><body>\n"
)

TOKEN_M = "\x00M{}\x00"
TOKEN_X = "\x00X{}\x00"


def extract(text: str, pattern: str, store: list[str], token: str,
            flags: int = 0) -> str:
    def repl(m: re.Match) -> str:
        store.append(m.group(0))
        return token.format(len(store) - 1)

    return re.sub(pattern, repl, text, flags=flags)


def convert(md_text: str) -> str:
    mermaid: list[str] = []
    text = extract(md_text, r"```mermaid[ \t]*\n(.*?)```", mermaid, TOKEN_M,
                   re.S)
    math: list[str] = []
    text = extract(text, r"\$\$.+?\$\$", math, TOKEN_X, re.S)
    text = extract(text, r"\$[^\$\n]+?\$", math, TOKEN_X)

    body = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists"]
    )

    body = re.sub(r"\x00X(\d+)\x00", lambda m: math[int(m.group(1))], body)

    for i, block in enumerate(mermaid):
        inner = re.sub(r"^```mermaid[ \t]*\n", "", block)
        inner = re.sub(r"```\s*$", "", inner).strip()
        div = f'<div class="mermaid">{inner}</div>'
        body = body.replace(f"<p>{TOKEN_M.format(i)}</p>", div)
        body = body.replace(TOKEN_M.format(i), div)
    return body


def build(md_path: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    html_body = convert(md_path.read_text(encoding="utf-8"))
    title = md_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / (md_path.stem + ".html")
    html_path = html_path.resolve()
    html_path.write_text(
        HEAD.replace("__TITLE__", html.escape(title)) + html_body
        + "\n</body></html>\n",
        encoding="utf-8",
    )

    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome is None:
        print("Chrome/Chromium not found; HTML written, PDF skipped.",
              file=sys.stderr)
        return html_path
    pdf_path = out_dir / (md_path.stem + ".pdf")
    pdf_path = pdf_path.resolve()
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer",
        "--virtual-time-budget=20000",
        f"--print-to-pdf={pdf_path}", html_path.as_uri(),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    return pdf_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("md", type=pathlib.Path)
    ap.add_argument("--out-dir", type=pathlib.Path, default=None)
    a = ap.parse_args()
    out_dir = a.out_dir or (a.md.parent / "html_pdf")
    pdf = build(a.md, out_dir)
    print(pdf)


if __name__ == "__main__":
    main()

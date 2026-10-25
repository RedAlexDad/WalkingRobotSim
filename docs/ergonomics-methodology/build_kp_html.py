#!/usr/bin/env python3
"""Build printable HTML versions of the two KR consultation documents.

The Markdown files remain the source of truth.  This script only prepares a
print-oriented artifact:

* Mermaid blocks are rendered to high-resolution PNG and embedded as data URIs,
  so the HTML is self-contained and does not need a browser-side Mermaid CDN;
* Pandoc converts the Markdown to HTML5 with MathML formulas;
* a print stylesheet provides A4 pages, Times New Roman, tables and captions.

Run it with the bundled Pandoc binary:

    uv run --with pypandoc_binary python build_kp_html.py

The script needs `mmdc` (Mermaid CLI) in PATH.  It is already used by the
repository for diagram checks.
"""

from __future__ import annotations

import base64
import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REACTION = ROOT / "reaction-time"


def _pandoc() -> str:
    """Return a Pandoc executable, preferring the pypandoc bundle."""
    try:
        import pypandoc  # type: ignore

        return pypandoc.get_pandoc_path()
    except Exception:
        path = shutil.which("pandoc")
        if not path:
            raise SystemExit(
                "Pandoc not found. Run with: "
                "uv run --with pypandoc_binary python build_kp_html.py"
            )
        return path


def _convert(markdown: str) -> str:
    """Convert GFM Markdown to an HTML fragment with MathML formulas."""
    with tempfile.TemporaryDirectory(prefix="kp-pandoc-") as td:
        src = Path(td) / "input.md"
        src.write_text(markdown, encoding="utf-8")
        cmd = [
            _pandoc(),
            str(src),
            "--from=gfm",
            "--to=html5",
            "--mathml",
            "--wrap=none",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Pandoc failed:\n{result.stderr}")
        return result.stdout


def _mermaid_config(font_size: int, *, wide: bool = False) -> dict:
    cfg = {
        "theme": "neutral",
        "securityLevel": "loose",
        "themeVariables": {
            "fontSize": f"{font_size}px",
            "fontFamily": "Times New Roman, Liberation Serif, DejaVu Serif, serif",
        },
        "flowchart": {
            "htmlLabels": False,
            "curve": "basis",
            "nodeSpacing": 40,
            "rankSpacing": 55,
        },
    }
    if wide:
        cfg["flowchart"]["nodeSpacing"] = 55
        cfg["flowchart"]["rankSpacing"] = 75
    return cfg


def _render_mermaid(
    code: str,
    *,
    orientation: str,
    font_size: int,
    wide: bool = False,
    workdir: Path,
    name: str,
) -> Path:
    """Render one Mermaid block to a 2x PNG and return its path."""
    mmdc = shutil.which("mmdc")
    if not mmdc:
        raise SystemExit("mmdc (Mermaid CLI) not found in PATH")

    if orientation == "TB":
        code = re.sub(r"^flowchart\s+LR\b", "flowchart TB", code, count=1)

    mmd = workdir / f"{name}.mmd"
    png = workdir / f"{name}.png"
    cfg_path = workdir / f"{name}.config.json"
    pup_path = workdir / "puppeteer.json"
    mmd.write_text(code, encoding="utf-8")
    cfg_path.write_text(
        json.dumps(_mermaid_config(font_size, wide=wide), ensure_ascii=False),
        encoding="utf-8",
    )
    pup_path.write_text(
        json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}),
        encoding="utf-8",
    )
    cmd = [
        mmdc,
        "-i",
        str(mmd),
        "-o",
        str(png),
        "-c",
        str(cfg_path),
        "-p",
        str(pup_path),
        "-b",
        "white",
        "-s",
        "2",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Mermaid failed for {name}:\n{result.stderr}")
    return png


def _figure_html(png: Path, caption: str, *, landscape: bool) -> str:
    data = base64.b64encode(png.read_bytes()).decode("ascii")
    alt = html.escape(caption, quote=True)
    cap = html.escape(caption)
    figure = (
        '<figure class="diagram">\n'
        f'<img src="data:image/png;base64,{data}" alt="{alt}">\n'
        f"<figcaption>{cap}</figcaption>\n"
        "</figure>"
    )
    if landscape:
        block = f'<div class="landscape-page">\n{figure}\n</div>'
    else:
        block = figure
    # Surround the raw HTML with blank lines so Pandoc closes the raw block
    # and continues parsing the following Markdown (headings, lists, etc.).
    return f"\n\n{block}\n\n"


DOCS = [
    {
        "source": REACTION / "2026-10-25_adaptive-recommender-kp.md",
        "output": REACTION / "2026-10-25_adaptive-recommender-kp.html",
        "figures": [
            {
                "orientation": "LR",
                "font_size": 20,
                "landscape": False,
                "caption": "Рис. 1. Структурная схема эргатической системы «Человек — Машина» (лекция 2).",
            },
            {
                "orientation": "LR",
                "font_size": 28,
                "landscape": True,
                "wide": True,
                "caption": "Рис. 2. Эргатическая система с адаптивным нейросетевым рекомендателем.",
            },
            {
                "orientation": "TB",
                "font_size": 20,
                "landscape": False,
                "caption": "Рис. 3. Классификация эргатических систем по уровням организации (лекция 2).",
            },
            {
                "orientation": "LR",
                "font_size": 20,
                "landscape": False,
                "caption": "Рис. 4. Контур адаптации поддержки.",
            },
        ],
    },
    {
        "source": REACTION / "2026-10-25_decision-stage-kp.md",
        "output": REACTION / "2026-10-25_decision-stage-kp.html",
        "figures": [
            {
                "orientation": "LR",
                "font_size": 20,
                "landscape": False,
                "caption": "Рис. 1. Структурная схема эргатической системы «Человек — Машина» (лекция 2).",
            },
            {
                "orientation": "TB",
                "font_size": 16,
                "landscape": False,
                "caption": "Рис. 2. Контур принятия решения оператором.",
            },
            {
                "orientation": "TB",
                "font_size": 20,
                "landscape": False,
                "caption": "Рис. 3. Классификация эргатических систем по уровням организации (лекция 2).",
            },
        ],
    },
]

CSS = r"""
@page {
  size: A4;
  margin: 18mm 16mm 18mm 20mm;
  @bottom-center {
    content: "— " counter(page) " —";
    font-family: "Times New Roman", "Liberation Serif", serif;
    font-size: 9pt;
    color: #000;
  }
}
@page :first {
  @bottom-center { content: none; }
}
@page landscape {
  size: A4 landscape;
  margin: 12mm 14mm 12mm 14mm;
}
* { box-sizing: border-box; }
html { font-size: 11pt; }
body {
  font-family: "Times New Roman", "Liberation Serif", "DejaVu Serif", serif;
  font-size: 11pt;
  line-height: 1.34;
  color: #000;
  margin: 0;
  overflow-wrap: break-word;
  hyphens: auto;
  -webkit-hyphens: auto;
}
@media screen {
  body {
    width: 21cm;
    margin: 0 auto;
    padding: 18mm 16mm 18mm 20mm;
    background: #fff;
  }
}
@media print {
  body { width: auto; margin: 0; padding: 0; }
  a { color: #000; text-decoration: none; }
}
h1 {
  font-size: 17pt;
  line-height: 1.22;
  text-align: center;
  font-weight: bold;
  margin: 0 0 8pt;
}
h1 + p {
  max-width: 16.2cm;
  margin: 0 auto 12pt;
  text-align: center;
  font-size: 10pt;
  line-height: 1.35;
}
h2 {
  font-size: 13.5pt;
  line-height: 1.22;
  font-weight: bold;
  margin: 14pt 0 6pt;
  break-after: avoid;
}
h3 {
  font-size: 12pt;
  line-height: 1.22;
  font-weight: bold;
  margin: 10pt 0 4pt;
  break-after: avoid;
}
h4 {
  font-size: 11pt;
  font-weight: bold;
  margin: 8pt 0 3pt;
  break-after: avoid;
}
p {
  margin: 0 0 5pt;
  text-align: justify;
  orphans: 2;
  widows: 2;
}
ul, ol { margin: 2pt 0 5pt 18pt; padding: 0; }
li { margin: 0 0 2.5pt; text-align: justify; }
li > p { margin: 0; }
hr { border: 0; border-top: 0.5pt solid #999; margin: 8pt 0; }
table {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
  font-size: 9.5pt;
  line-height: 1.2;
  margin: 6pt 0 10pt;
}
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td {
  border: 0.5pt solid #000;
  padding: 2pt 3pt;
  vertical-align: top;
  overflow-wrap: break-word;
}
th { background: #e8e8e8; font-weight: bold; text-align: center; }
td { text-align: left; }
code {
  font-family: "Courier New", "Liberation Mono", monospace;
  font-size: 9.5pt;
  overflow-wrap: anywhere;
}
pre {
  font-family: "Courier New", "Liberation Mono", monospace;
  font-size: 8pt;
  line-height: 1.2;
  background: #f5f5f5;
  border: 0.5pt solid #999;
  padding: 4pt;
  white-space: pre-wrap;
  break-inside: avoid;
}
blockquote {
  margin: 5pt 0 5pt 12pt;
  padding: 2pt 0 2pt 8pt;
  border-left: 2pt solid #999;
  text-align: left;
}
blockquote p { text-align: left; }
math { font-size: 105%; }
math[display="block"] {
  display: inline-block;
  margin: 5pt 0;
  max-width: 100%;
}
p:has(> math[display="block"]) {
  text-align: center;
  break-before: avoid;
  break-inside: avoid;
}
p:has(+ p > math[display="block"]) { break-after: avoid; }
a { color: #000; text-decoration: none; }
figure.diagram {
  margin: 8pt 0 11pt;
  text-align: center;
  break-inside: avoid;
}
figure.diagram img {
  max-width: 100%;
  max-height: 220mm;
  width: auto;
  height: auto;
}
figure.diagram figcaption {
  margin-top: 4pt;
  font-size: 9.5pt;
  line-height: 1.25;
  text-align: center;
}
.landscape-page {
  page: landscape;
  break-before: page;
  break-after: page;
  padding-top: 45mm;
}
.landscape-page figure.diagram {
  margin: 0;
}
.landscape-page figure.diagram img {
  width: 100%;
  max-height: 160mm;
  object-fit: contain;
}
.landscape-page figure.diagram figcaption {
  font-size: 10pt;
  margin-top: 6pt;
}
h2[id="1-резюме"],
h2[id="14-источники"],
h2[id="15-приложение-схемы"],
h2[id="17-источники"],
h2[id="18-приложение-схемы"] {
  break-before: page;
  margin-top: 0;
}
"""


def build(spec: dict) -> None:
    source: Path = spec["source"]
    output: Path = spec["output"]
    figures = spec["figures"]
    markdown = source.read_text(encoding="utf-8")
    pattern = re.compile(r"^```mermaid\s*\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)
    matches = list(pattern.finditer(markdown))
    if len(matches) != len(figures):
        raise SystemExit(
            f"{source.name}: found {len(matches)} Mermaid blocks, "
            f"expected {len(figures)}"
        )

    with tempfile.TemporaryDirectory(prefix="kp-mermaid-") as td:
        workdir = Path(td)
        replacements: list[tuple[re.Match, str]] = []
        for index, (match, figure) in enumerate(zip(matches, figures), start=1):
            code = match.group(1)
            png = _render_mermaid(
                code,
                orientation=figure["orientation"],
                font_size=figure["font_size"],
                wide=figure.get("wide", False),
                workdir=workdir,
                name=f"fig{index}",
            )
            replacements.append(
                (
                    match,
                    _figure_html(
                        png,
                        figure["caption"],
                        landscape=figure.get("landscape", False),
                    ),
                )
            )

        # Replace from the end so earlier offsets remain valid.
        prepared = markdown
        for match, replacement in reversed(replacements):
            prepared = prepared[: match.start()] + replacement + prepared[match.end() :]

    body = _convert(prepared)
    # A landscape figure is forced onto its own page.  Move the immediately
    # preceding h3 inside that page so the section title is not left orphaned
    # at the bottom of the portrait page.
    body = re.sub(
        r'(<h3[^>]*>[^<]*</h3>)\s*(<div class="landscape-page">)',
        r'\2\n\1',
        body,
        count=1,
    )
    title = source.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
    document = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="author" content="Папин А.В., группа ИУ5Ц-31М">
<meta name="description" content="Материалы к консультации по курсовой работе: эргономические требования и характеристики.">
<style>
{CSS}
</style>
</head>
<body>
{body}
</body>
</html>
"""
    output.write_text(document, encoding="utf-8")
    size_kb = output.stat().st_size / 1024
    print(f"built {output.relative_to(ROOT)} ({size_kb:.0f} KiB)")


def main() -> None:
    for spec in DOCS:
        build(spec)


if __name__ == "__main__":
    main()

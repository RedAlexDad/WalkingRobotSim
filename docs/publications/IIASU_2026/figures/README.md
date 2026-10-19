# Figure 1 — IEEE/REEPE format

## Files

- `fig1-methodology.pdf` — векторный PDF, шрифты встроены
  (`TimesNewRomanPSMT`, `TimesNewRomanPS-BoldMT`);
- `fig1-methodology.eps` — векторный EPS;
- `fig1-methodology.png` — 2148×960 px, 300 dpi;
- `fig1-methodology.tif` — 300 dpi, LZW;
- `make_fig1.py` — исходник (matplotlib, Times New Roman 8 pt).

## Format

- **7.16 × 3.2 in** (2148×960 px при 300 dpi), IEEE double column;
- **300 dpi** TIFF/PNG; векторные PDF/EPS для подачи;
- **Times New Roman 8 pt**, шрифты встроены;
- **чёрно-белая** графика, тонкие линии 0.6 pt;
- прямоугольные блоки, номера этапов 1–6, ортогональные связи,
  формулы (Ψ, число Борда, средний ранг);
- подпись **под рисунком**, **8 pt Times New Roman**;
- в `article.docx` рисунок вставлен на ширину **16 см**;
- в IEEE/REEPE — `Fig. 1`; в ИИАСУ — `Рис. 1`.

## Captions

RU: **Рис. 1.** Структурная схема методики выбора модели.

EN: **Fig. 1.** Block diagram of the model selection methodology.

## Note

В Markdown размер шрифта подписи не задаётся. При сборке `.docx`
поставить подпись 8 pt Times New Roman и разместить рисунок вверху
или внизу колонки/страницы (требование IEEE).

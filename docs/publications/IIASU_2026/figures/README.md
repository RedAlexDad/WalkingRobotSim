# Figure 1 — IEEE/REEPE format

## Files

Основной вариант (как `REEPE_2027/figures/bw`, 3.76 × 5.28 in):

- `fig1-methodology.pdf` — векторный PDF, шрифты встроены
  (`TimesNewRomanPSMT`);
- `fig1-methodology.eps` — векторный EPS;
- `fig1-methodology.png` — 1128×1584 px, 300 dpi;
- `fig1-methodology.tif` — 300 dpi, LZW.

Дополнительный вариант (IEEE double column):

- `fig1-methodology-wide.pdf`;
- `fig1-methodology-wide.eps`;
- `fig1-methodology-wide.png` — 2148×960 px, 300 dpi;
- `fig1-methodology-wide.tif` — 300 dpi, LZW.

Исходник: `make_fig1.py` (matplotlib, Times New Roman 8 pt).

## Format

- Основной рисунок — **3.76 × 5.28 in** (1128×1584 px при 300 dpi),
  как рисунки в `REEPE_2027/figures/bw/`;
- широкий — **7.16 × 3.2 in** (double column IEEE);
- **300 dpi** TIFF/PNG; векторные PDF/EPS для подачи;
- **Times New Roman 8 pt**, шрифты встроены;
- **чёрно-белый**, читается без цвета;
- подпись **под рисунком**, **8 pt Times New Roman**;
- в IEEE/REEPE — `Fig. 1`; в ИИАСУ — `Рис. 1`.

## Captions

RU: **Рис. 1.** Схема методики выбора модели.

EN: **Fig. 1.** Model selection methodology.

## Note

В Markdown размер шрифта подписи не задаётся. При сборке `.docx`
поставить подпись 8 pt Times New Roman и разместить рисунок вверху
или внизу колонки/страницы (требование IEEE).

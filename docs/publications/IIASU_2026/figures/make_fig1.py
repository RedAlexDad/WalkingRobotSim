"""Рис. 1: горизонтальная академическая блок-схема методики.

IEEE/REEPE:
- 7.16 × 3.2 in (double column), 300 dpi;
- Times New Roman 8 pt, ч/б, тонкие линии 0.6 pt;
- прямоугольные блоки, номера этапов, ортогональные связи, формулы;
- подпись под рисунком 8 pt TNR.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 8,
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 7.16, 3.2

fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")


def box(x, y, w, h, text, fs=8, dashed=False):
    ax.add_patch(Rectangle(
        (x, y), w, h, fill=False, edgecolor="black", linewidth=0.6,
        linestyle=(0, (3, 2)) if dashed else "solid",
    ))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, linespacing=1.10)


def ortho(points, dashed=False):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    style = (0, (2, 2)) if dashed else "solid"
    ax.plot(xs[:-1], ys[:-1], color="black", linewidth=0.6,
            linestyle=style, solid_capstyle="butt")
    ax.add_patch(FancyArrowPatch(
        points[-2], points[-1], arrowstyle="-|>", mutation_scale=6,
        linewidth=0.6, color="black", linestyle=style,
        shrinkA=0, shrinkB=0,
    ))


def stage(x, y, n):
    ax.text(x, y, n, ha="left", va="bottom", fontsize=8, fontweight="bold")


box(0.08, 2.10, 1.05, 0.70, "Кандидаты:\n7 моделей")
stage(0.10, 2.83, "1")

box(1.30, 2.10, 1.30, 0.70,
    "Отсев по требованиям\nборта:\nT ≤ 0,1 с; M ≤ 64 МБ")
stage(1.32, 2.83, "2")

box(2.78, 2.10, 1.42, 0.70,
    "Характеристики\nархитектуры:\nP, F, mAP, M, T")
stage(2.80, 2.83, "3")

box(4.42, 2.38, 1.38, 0.64,
    "Критерии\nнеопределённости:\nWald, Savage,\nHurwicz")
stage(4.44, 3.05, "4a")

box(4.42, 1.55, 1.38, 0.64,
    "Авторские метрики:\nQ4, BF, DF,\nAR, APM")
stage(4.44, 2.22, "4b")

box(6.00, 2.10, 1.06, 0.70,
    "Свёртка:\nΨ, Борда,\nсредний ранг")
stage(6.02, 2.83, "5")

box(6.00, 1.25, 1.06, 0.42, "Решение:\nYOLO11n")
box(0.08, 0.35, 6.98, 0.45,
    "Верификация: Gazebo (4 сцены), кафе, COCO128", dashed=True)
stage(0.10, 0.82, "6")

ortho([(1.13, 2.45), (1.30, 2.45)])
ortho([(2.60, 2.45), (2.78, 2.45)])
ortho([(4.20, 2.60), (4.30, 2.60), (4.30, 2.71), (4.42, 2.71)])
ortho([(4.20, 2.30), (4.30, 2.30), (4.30, 1.88), (4.42, 1.88)])
ortho([(5.80, 2.71), (5.90, 2.71), (5.90, 2.55), (6.00, 2.55)])
ortho([(5.80, 1.88), (5.90, 1.88), (5.90, 2.25), (6.00, 2.25)])
ortho([(6.53, 2.10), (6.53, 1.67)])
ortho([(6.53, 1.25), (6.53, 0.80)], dashed=True)

for ext in ("pdf", "png", "tif", "eps"):
    path = os.path.join(OUT, f"fig1-methodology.{ext}")
    fig.savefig(path, dpi=300, facecolor="white")
    print("saved", path)
plt.close(fig)

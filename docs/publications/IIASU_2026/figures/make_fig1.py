"""Рис. 1: академическая блок-схема методики выбора модели.

IEEE/REEPE:
- 3.76 × 5.28 in (как figures/bw в REEPE), 300 dpi;
- Times New Roman 8 pt, ч/б, тонкие линии 0.6 pt;
- прямоугольные блоки, нумерация этапов, ортогональные связи, формулы;
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
W, H = 3.76, 5.28

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
            fontsize=fs, linespacing=1.12)


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


# этапная линейка
ax.plot([0.20, 0.20], [0.32, 5.00], color="black", linewidth=0.5)
for y, n in [(4.775, "1"), (3.975, "2"), (2.72, "3"),
             (1.275, "4"), (0.575, "5")]:
    ax.text(0.11, y, n, ha="center", va="center",
            fontsize=8, fontweight="bold")

# блоки
box(0.42, 4.55, 3.18, 0.45, "Кандидаты: 7 моделей")
box(0.42, 3.70, 3.18, 0.55, "Отсев по требованиям борта\nT ≤ 0,1 с; M ≤ 64 МБ")
box(0.42, 2.80, 3.18, 0.55, "Характеристики архитектуры\nP, F, mAP, M, T")

box(0.42, 1.85, 1.52, 0.80,
    "Критерии\nнеопределённости\nWald, Savage,\nHurwicz")
box(2.08, 1.85, 1.52, 0.80,
    "Авторские\nметрики\nQ4, BF, DF,\nAR, APM")

box(0.42, 0.95, 3.18, 0.65, "")
ax.text(2.01, 1.48, "Свёртка критериев", ha="center", va="center", fontsize=8)
ax.text(2.01, 1.27,
        r"$\Psi_i=\frac{1}{K}\sum_{k=1}^{K}z_i^{(k)}$",
        ha="center", va="center", fontsize=8)
ax.text(2.01, 1.09,
        r"$B_i$ (Борда), $\bar r_i$ (средний ранг)",
        ha="center", va="center", fontsize=8)

box(0.42, 0.40, 3.18, 0.35, "Решение: YOLO11n")
box(0.42, 0.05, 3.18, 0.25,
    "Верификация: Gazebo, кафе, COCO128", dashed=True)

# связи
ortho([(2.01, 4.55), (2.01, 4.25)])
ortho([(2.01, 3.70), (2.01, 3.35)])
ortho([(2.01, 2.80), (2.01, 2.72)])
ortho([(2.01, 2.72), (1.18, 2.72), (1.18, 2.65)])
ortho([(2.01, 2.72), (2.84, 2.72), (2.84, 2.65)])
ortho([(1.18, 1.85), (1.18, 1.75), (2.01, 1.75)])
ortho([(2.84, 1.85), (2.84, 1.75), (2.01, 1.75)])
ortho([(2.01, 1.75), (2.01, 1.60)])
ortho([(2.01, 0.95), (2.01, 0.75)])
ortho([(2.01, 0.40), (2.01, 0.30)], dashed=True)

for ext in ("pdf", "png", "tif", "eps"):
    path = os.path.join(OUT, f"fig1-methodology.{ext}")
    fig.savefig(path, dpi=300, facecolor="white")
    print("saved", path)
plt.close(fig)

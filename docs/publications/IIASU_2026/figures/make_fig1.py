"""Рис. 1: схема методики выбора модели.

Формат IEEE/REEPE:
- основной вариант: 3.76 × 5.28 in (как figures/bw в REEPE), 300 dpi;
- дополнительный: 7.16 × 3.2 in (double column);
- Times New Roman 8 pt, ч/б, подпись под рисунком 8 pt TNR.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

OUT = os.path.dirname(os.path.abspath(__file__))


def new_fig(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fs=8):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=0.8, edgecolor="black", facecolor="white",
    ))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, linespacing=1.15)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=7,
        linewidth=0.8, color="black", shrinkA=0, shrinkB=0,
    ))


def save(fig, name):
    for ext in ("pdf", "png", "tif", "eps"):
        path = os.path.join(OUT, f"{name}.{ext}")
        fig.savefig(path, dpi=300, facecolor="white")
        print("saved", path)
    plt.close(fig)


def single_column():
    w, h = 3.76, 5.28
    fig, ax = new_fig(w, h)
    box(ax, 0.13, 4.55, 3.50, 0.50, "Модели-кандидаты (7)")
    box(ax, 0.13, 3.75, 3.50, 0.55, "Фильтры борта:\nT ≤ 0,1 с; M ≤ 64 МБ")
    box(ax, 0.13, 3.00, 3.50, 0.55,
        "Характеристики архитектуры:\nP, F, mAP, M, T")
    box(ax, 0.13, 2.15, 1.65, 0.60, "Критерии\nнеопределённости")
    box(ax, 1.98, 2.15, 1.65, 0.60, "Авторские\nметрики")
    box(ax, 0.13, 1.30, 3.50, 0.55,
        "Итоговое сведение:\nΨ, Борда, средний ранг")
    box(ax, 0.13, 0.65, 3.50, 0.45, "Выбор: YOLO11n")
    box(ax, 0.13, 0.05, 3.50, 0.45,
        "Проверка: Gazebo, кафе, COCO128")

    arrow(ax, 1.88, 4.55, 1.88, 4.30)
    arrow(ax, 1.88, 3.75, 1.88, 3.55)
    arrow(ax, 1.88, 3.00, 0.955, 2.75)
    arrow(ax, 1.88, 3.00, 2.805, 2.75)
    arrow(ax, 0.955, 2.15, 1.88, 1.85)
    arrow(ax, 2.805, 2.15, 1.88, 1.85)
    arrow(ax, 1.88, 1.30, 1.88, 1.10)
    arrow(ax, 1.88, 0.65, 1.88, 0.50)
    save(fig, "fig1-methodology")


def wide():
    w, h = 7.16, 3.2
    fig, ax = new_fig(w, h)
    box(ax, 0.05, 1.55, 1.15, 0.75, "Модели-\nкандидаты\n(7)")
    box(ax, 1.45, 1.55, 1.25, 0.75, "Фильтры борта:\nT ≤ 0,1 с\nM ≤ 64 МБ")
    box(ax, 2.95, 1.55, 1.45, 0.75,
        "Характеристики\nархитектуры:\nP, F, mAP, M, T")
    box(ax, 4.65, 2.15, 1.35, 0.65, "Критерии\nнеопределённости")
    box(ax, 4.65, 1.05, 1.35, 0.65, "Авторские\nметрики")
    box(ax, 6.15, 1.55, 0.95, 0.75, "Сведение:\nΨ, Борда,\nсредний ранг")
    box(ax, 6.15, 0.75, 0.95, 0.55, "Выбор:\nYOLO11n")
    box(ax, 6.15, 0.05, 0.95, 0.50, "Проверка:\nGazebo, кафе,\nCOCO128")

    arrow(ax, 1.20, 1.925, 1.45, 1.925)
    arrow(ax, 2.70, 1.925, 2.95, 1.925)
    arrow(ax, 4.40, 2.10, 4.65, 2.40)
    arrow(ax, 4.40, 1.80, 4.65, 1.45)
    arrow(ax, 6.00, 2.40, 6.15, 2.10)
    arrow(ax, 6.00, 1.45, 6.15, 1.80)
    arrow(ax, 6.625, 1.55, 6.625, 1.30)
    arrow(ax, 6.625, 0.75, 6.625, 0.55)
    save(fig, "fig1-methodology-wide")


if __name__ == "__main__":
    single_column()
    wide()

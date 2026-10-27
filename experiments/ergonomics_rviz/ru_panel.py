#!/usr/bin/env python3
"""Русская боковая панель для рисунков отчёта.

RViz не рендерит кириллицу в текстовых маркерах (проверено: «TEST»
рисуется, «ТЕСТ» — нет), а текстура на mesh-кваде не привязывается.
Поэтому панель отрисовывается здесь и накладывается на снимок RViz
поверх английских панелей. Это подготовка рисунка, а не живой UI;
в подписи к рисунку это должно быть указано.

Координаты соответствуют конфигу im_operator_sim.rviz:
вид TopDownOrtho, Scale 120, X 4.5, Y -2.1, окно 3456x2160.
Панели занимают x 6.0..15.6 м, y -10.7..6.8 м.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 3456, 2160
PX_PER_M = 120.0
VIEW_X, VIEW_Y = 4.5, -2.1

PANEL_LEFT = 6.0
PANEL_RIGHT = 15.6
PANEL_TOP = 6.8
PANEL_BOTTOM = -10.7

BG = (15, 15, 15)
BORDER = (191, 191, 191)
WHITE = (255, 255, 255)
COL_CURRENT = (199, 99, 0)
COL_NEXT = (0, 128, 255)
COL_OTHER = (140, 140, 140)
COL_PATH = (0, 102, 0)
COL_OBS = (158, 13, 13)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

STATES = {
    "normal": {
        "panel": (0, 77, 0),
        "event": "СИСТЕМА В НОРМЕ",
        "cause": "НЕТ",
        "action": "НЕТ",
        "deadline": "Н/Д",
        "state": "НОРМА",
        "robot": "ГОТОВ",
    },
    "confirm": {
        "panel": (82, 5, 5),
        "event": "ТРЕБУЕТСЯ ПОДТВЕРЖДЕНИЕ",
        "cause": "НУЖЕН ПЕРЕПЛАН",
        "action": "ДА / НЕТ",
        "deadline": "2,5 с",
        "state": "ПОДТВЕРЖДЕНИЕ",
        "robot": "ОЖИДАНИЕ",
    },
    "confirmed": {
        "panel": (0, 77, 0),
        "event": "ПОДТВЕРЖДЕНО",
        "cause": "ОПЕРАТОР",
        "action": "СЛЕД. УЧАСТОК",
        "deadline": "Н/Д",
        "state": "ПОДТВЕРЖДЕНО",
        "robot": "ПОДТВЕРЖДЁН",
    },
    "cancelled": {
        "panel": (97, 56, 0),
        "event": "ОТМЕНЕНО",
        "cause": "ОПЕРАТОР",
        "action": "УДЕРЖАНИЕ",
        "deadline": "Н/Д",
        "state": "ОТМЕНЕНО",
        "robot": "УДЕРЖАНИЕ",
    },
    "stuck": {
        "panel": (82, 5, 5),
        "event": "ЗАСТРЯЛ ПЕРЕД ПРЕПЯТСТВИЕМ",
        "cause": "ПРЕПЯТСТВИЕ",
        "action": "ДА / НЕТ",
        "deadline": "2,5 с",
        "state": "ЗАСТРЯЛ",
        "robot": "БЛОКИРОВАН",
    },
}


def to_px(x: float, y: float) -> tuple[float, float]:
    return (
        (x - VIEW_X) * PX_PER_M + W / 2,
        (VIEW_Y - y) * PX_PER_M + H / 2,
    )


def box(draw: ImageDraw.ImageDraw, x0: float, y0: float, x1: float, y1: float,
        fill: tuple[int, int, int]) -> None:
    px0, py0 = to_px(x0, y0)
    px1, py1 = to_px(x1, y1)
    draw.rectangle([px0, py0, px1, py1], fill=fill, outline=BORDER, width=3)


def text(draw: ImageDraw.ImageDraw, x: float, y: float, value: str, size_px: int,
         color: tuple[int, int, int] = WHITE, anchor: str = "mm",
         max_width: int = 1090) -> None:
    size = size_px
    while size > 20:
        font = ImageFont.truetype(FONT_PATH, size)
        if draw.textlength(value, font=font) <= max_width:
            break
        size -= 2
    font = ImageFont.truetype(FONT_PATH, size)
    px, py = to_px(x, y)
    draw.text((px, py), value, font=font, fill=color, anchor=anchor)


def render(state: str, out: Path) -> None:
    cfg = STATES[state]
    img = Image.new("RGB", (W, H), (40, 40, 40))
    draw = ImageDraw.Draw(img)

    size_main = int(0.76 * PX_PER_M)      # 91 px, как text_scale 0.76
    size_second = int(0.608 * PX_PER_M)   # 73 px
    size_title = int(0.57 * PX_PER_M)     # 68 px

    # легенда
    box(draw, PANEL_LEFT, PANEL_TOP, PANEL_RIGHT, 1.8, BG)
    text(draw, 10.8, 6.25, "ЛЕГЕНДА", size_title)
    items = [
        ("ТЕКУЩАЯ", COL_CURRENT, 5.2),
        ("СЛЕДУЮЩАЯ", COL_NEXT, 4.42),
        ("ОСТАЛЬНЫЕ", COL_OTHER, 3.64),
        ("ПУТЬ", COL_PATH, 2.86),
        ("ПРЕПЯТСТВИЕ", COL_OBS, 2.08),
    ]
    for label, color, y in items:
        sx, sy = to_px(7.9, y)
        draw.rectangle([sx - 25, sy - 25, sx + 25, sy + 25], fill=color)
        text(draw, 10.6, y, label, size_second)

    # событие
    box(draw, PANEL_LEFT, 0.1, PANEL_RIGHT, -4.0, cfg["panel"])
    text(draw, 10.8, -0.45, "СОБЫТИЕ", size_main)
    text(draw, 10.8, -1.13, cfg["event"], size_main)
    text(draw, 10.8, -1.81, f"ПРИЧИНА: {cfg['cause']}", size_main)
    text(draw, 10.8, -2.49, f"ДЕЙСТВИЕ: {cfg['action']}", size_main)
    text(draw, 10.8, -3.17, f"СРОК: {cfg['deadline']}", size_main)

    # статус
    box(draw, PANEL_LEFT, -5.7, PANEL_RIGHT, PANEL_BOTTOM, BG)
    text(draw, 10.8, -6.3, "РЕЖИМ: НАДЗОР", size_main)
    text(draw, 10.8, -7.1, "WP: 8 ЗАГРУЖЕНО", size_main)
    text(draw, 10.8, -7.9, f"СОСТОЯНИЕ: {cfg['state']}", size_main)
    text(draw, 10.8, -8.7, f"РОБОТ: {cfg['robot']}", size_main)
    text(draw, 10.8, -9.5, "СВЯЗЬ: ОК", size_main)

    img.save(out)
    print(f"панель: {out}")


def composite(screenshot: Path, panel: Path, out: Path) -> None:
    base = Image.open(screenshot).convert("RGB")
    img = Image.open(panel).convert("RGB")
    left, top = to_px(PANEL_LEFT, PANEL_TOP)
    right, bottom = to_px(PANEL_RIGHT, PANEL_BOTTOM)
    crop = img.crop((int(left), int(top), int(right), int(bottom)))
    base.paste(crop, (int(left), int(top)))
    base.save(out)
    print(f"рисунок: {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", choices=sorted(STATES))
    parser.add_argument("--shot", type=Path, help="снимок RViz для наложения")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--panel-out", type=Path)
    args = parser.parse_args()

    panel_out = args.panel_out or Path(f"/tmp/ru_panel_{args.state}.png")
    render(args.state, panel_out)
    if args.shot:
        composite(args.shot, panel_out, args.out)


if __name__ == "__main__":
    main()

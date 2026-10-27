#!/usr/bin/env python3
"""Русская боковая панель ИМ поверх окна RViz.

RViz не рендерит кириллицу в текстовых маркерах (проверено: TEST
рисуется, ТЕСТ — нет). Поэтому панель отрисовывается отдельным
окном Qt без рамки, поверх правой части окна RViz: легенда,
событие, статус. Данные берутся из /im_state и /waypoint_state.

Геометрия по умолчанию соответствует полноэкранному RViz
(0,720) 3456x2160 с видом TopDownOrtho Scale 120, X 4.5, Y -2.1:
панели занимают x 6.0..15.6 м, y -10.7..6.8 м.
"""

from __future__ import annotations

import argparse
import json
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from PyQt5.QtCore import QRect, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QWidget

PANEL_W = 1152
PANEL_H = 2100
BG = QColor(15, 15, 15)
BORDER = QColor(191, 191, 191)
WHITE = QColor(255, 255, 255)
SWATCHES = [
    ("ТЕКУЩАЯ", QColor(199, 99, 0)),
    ("СЛЕДУЮЩАЯ", QColor(0, 128, 255)),
    ("ОСТАЛЬНЫЕ", QColor(140, 140, 140)),
    ("ПУТЬ", QColor(0, 102, 0)),
    ("ПРЕПЯТСТВИЕ", QColor(158, 13, 13)),
]
STATES = {
    "normal": dict(panel=QColor(0, 77, 0), event="СИСТЕМА В НОРМЕ",
                   cause="НЕТ", action="НЕТ", deadline="Н/Д",
                   state="НОРМА", robot="ГОТОВ"),
    "confirm": dict(panel=QColor(82, 5, 5), event="ТРЕБУЕТСЯ ПОДТВЕРЖДЕНИЕ",
                    cause="НУЖЕН ПЕРЕПЛАН", action="ДА / НЕТ", deadline="2,5 с",
                    state="ПОДТВЕРЖДЕНИЕ", robot="ОЖИДАНИЕ"),
    "confirmed": dict(panel=QColor(0, 77, 0), event="ПОДТВЕРЖДЕНО",
                      cause="ОПЕРАТОР", action="СЛЕД. УЧАСТОК", deadline="Н/Д",
                      state="ПОДТВЕРЖДЕНО", robot="ПОДТВЕРЖДЁН"),
    "cancelled": dict(panel=QColor(97, 56, 0), event="ОТМЕНЕНО",
                      cause="ОПЕРАТОР", action="УДЕРЖАНИЕ", deadline="Н/Д",
                      state="ОТМЕНЕНО", robot="УДЕРЖАНИЕ"),
    "stuck": dict(panel=QColor(82, 5, 5), event="ЗАСТРЯЛ ПЕРЕД ПРЕПЯТСТВИЕМ",
                  cause="ПРЕПЯТСТВИЕ", action="ДА / НЕТ", deadline="2,5 с",
                  state="ЗАСТРЯЛ", robot="БЛОКИРОВАН"),
}


class RosBridge(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.state = "normal"
        self.wp_text = "WP: НЕТ"
        self.version = 0

    def run(self) -> None:
        rclpy.init()
        node = Node("ru_hud")
        node.create_subscription(String, "/im_state", self.on_state, 10)
        node.create_subscription(String, "/waypoint_state", self.on_wp, 10)
        rclpy.spin(node)

    def _bump(self) -> None:
        with self.lock:
            self.version += 1

    def on_state(self, msg: String) -> None:
        value = msg.data.strip().lower()
        if value in STATES:
            with self.lock:
                self.state = value
            self._bump()

    def on_wp(self, msg: String) -> None:
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        count = int(data.get("count", 0))
        active = bool(data.get("active"))
        current = int(data.get("current", 0))
        if count == 0:
            text = "WP: НЕТ"
        elif active:
            cur = current % count + 1
            nxt = (current + 1) % count + 1
            text = f"WP: {cur} → {nxt}"
        else:
            text = f"WP: {count} ЗАГРУЖЕНО"
        with self.lock:
            self.wp_text = text
        self._bump()


class Panel(QWidget):
    def __init__(self, bridge: RosBridge, geometry: tuple[int, int, int, int]) -> None:
        super().__init__()
        self.bridge = bridge
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setGeometry(*geometry)
        self.seen_version = -1
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(120)

    def poll(self) -> None:
        with self.bridge.lock:
            version = self.bridge.version
        if version != self.seen_version:
            self.seen_version = version
            self.update()

    def fit(self, painter: QPainter, text: str, size: int, width: int = 1090) -> QFont:
        font = QFont("DejaVu Sans")
        font.setPixelSize(size)
        while font.pixelSize() > 20:
            if QFontMetrics(font).horizontalAdvance(text) <= width:
                break
            font.setPixelSize(font.pixelSize() - 2)
        return font

    def line(self, painter: QPainter, x: int, y: int, text: str, size: int,
             color: QColor = WHITE, width: int = 1090) -> None:
        font = self.fit(painter, text, size, width)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(QRect(x - 545, y - size, 1090, size * 2),
                         Qt.AlignHCenter | Qt.AlignVCenter, text)

    def box(self, painter: QPainter, y0: int, y1: int, fill: QColor) -> None:
        painter.fillRect(QRect(0, y0, PANEL_W, y1 - y0), fill)
        painter.setPen(QPen(BORDER, 3))
        painter.drawRect(QRect(0, y0, PANEL_W - 1, y1 - y0 - 1))

    def paintEvent(self, event) -> None:  # noqa: N802
        with self.bridge.lock:
            state = self.bridge.state
            wp_text = self.bridge.wp_text
        cfg = STATES.get(state, STATES["normal"])
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # фон промежутков — как у RViz
        p.fillRect(self.rect(), QColor(40, 40, 40))

        # легенда
        self.box(p, 0, 600, BG)
        self.line(p, PANEL_W // 2, 66, "УСЛОВНЫЕ ОБОЗНАЧЕНИЯ", 68)
        for i, (label, color) in enumerate(SWATCHES):
            y = 192 + i * 94
            p.fillRect(QRect(228 - 25, y - 25, 50, 50), color)
            self.line(p, 552, y, label, 73)

        # событие
        self.box(p, 804, 1296, cfg["panel"])
        self.line(p, PANEL_W // 2, 804 + 66, "СОБЫТИЕ", 91)
        self.line(p, PANEL_W // 2, 804 + 148, cfg["event"], 91)
        self.line(p, PANEL_W // 2, 804 + 229, f"ПРИЧИНА: {cfg['cause']}", 91)
        self.line(p, PANEL_W // 2, 804 + 311, f"ДЕЙСТВИЕ: {cfg['action']}", 91)
        self.line(p, PANEL_W // 2, 804 + 392, f"СРОК: {cfg['deadline']}", 91)

        # статус
        self.box(p, 1500, 2100, BG)
        self.line(p, PANEL_W // 2, 1500 + 72, "РЕЖИМ: НАДЗОР", 91)
        self.line(p, PANEL_W // 2, 1500 + 168, wp_text, 91)
        self.line(p, PANEL_W // 2, 1500 + 264, f"СОСТОЯНИЕ: {cfg['state']}", 91)
        self.line(p, PANEL_W // 2, 1500 + 360, f"РОБОТ: {cfg['robot']}", 91)
        self.line(p, PANEL_W // 2, 1500 + 456, "СВЯЗЬ: ОК", 91)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--x", type=int, default=1908)
    parser.add_argument("--y", type=int, default=732)
    parser.add_argument("--w", type=int, default=PANEL_W)
    parser.add_argument("--h", type=int, default=PANEL_H)
    args = parser.parse_args()

    bridge = RosBridge()
    bridge.start()

    app = QApplication([])
    panel = Panel(bridge, (args.x, args.y, args.w, args.h))
    panel.show()
    app.exec_()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Генерация `make help` из комментариев рядом с целями.

Соглашения:
    ##  Описание   — цель попадает в справку (make <цель>)
    ##! Описание   — цель скрыта из справки

Разделы и порядок заданы в SECTIONS ниже.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECTIONS: list[tuple[str, list[str], str | None]] = [
    ("Основные команды", ["Makefile"], None),
    ("Docker / контейнер", ["makefiles/docker.mk"],
     "Аргументы: NO_CACHE=1 — сборка без кэша (build); BG=1 — запуск в фоне "
     "без ожидания ROS (up); STAGE=<этап> — этап сборки (build-stage)"),
    ("Диагностика", ["makefiles/safety.mk"], None),
    ("ROS MCP", ["makefiles/mcp.mk"], None),
    ("Микросервисы Docker", ["makefiles/microservices.mk"],
     "Аргумент: SVC=sim|core|nav|rviz — только один сервис (по умолчанию все)"),
    ("Симуляция Gazebo", ["makefiles/simulation.mk"],
     "Аргументы: teleop SIMPLE=1 (простой), VX/WZ — скорость; set-pose X=.. Y=.. "
     "Z=.. YAW=..; exec CMD=\"...\"; clean-logs WHAT=build|gazebo"),
    ("Состояния робота", ["makefiles/controller.mk"], None),
    ("Waypoint навигация", ["makefiles/navigation.mk"], None),
    ("Эксперименты", ["makefiles/experiment.mk"], None),
    ("YOLO", ["makefiles/yolo.mk"], None),
    ("Elevation Mapping", ["makefiles/elevation.mk"],
     "Аргумент: CPU=1 — CPU-образ (по умолчанию GPU)"),
    ("Сборка и тесты", ["makefiles/rust.mk", "makefiles/test.mk"],
     "Аргументы: test TARGET=rust|sim|coverage|correctness|benchmark; "
     "check WHAT=deps|structure|yaml|x11; benchmark WHAT=cpp|python"),
    ("CI и линт", ["makefiles/ci.mk"],
     "Аргументы: LINT=yaml|python|cpp — одна проверка (по умолчанию все); "
     "TEST=cpp — только C++ тесты"),
    ("NVIDIA", ["makefiles/nvidia.mk"], None),
]

GREEN, GREY, BOLD, NC = "\033[0;32m", "\033[0;90m", "\033[1m", "\033[0m"
TARGET_RE = re.compile(r"^([A-Za-z0-9_-]+):")


def entries(path: Path) -> list[tuple[str, str]]:
    """Пары (цель, первое описание '##') из файла; '##!' скрывает."""
    out: list[tuple[str, str]] = []
    desc: str | None = None
    hidden = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("##! "):
            hidden, desc = True, None
        elif line.startswith("## "):
            if not hidden and desc is None:
                desc = line[3:].strip()
        else:
            m = TARGET_RE.match(line)
            if m and desc and not hidden:
                out.append((m.group(1), desc))
            desc, hidden = None, False
    return out


def main() -> None:
    print()
    print(f"{BOLD}Walking Robot Simulation Manager{NC}")
    for title, files, hint in SECTIONS:
        rows: list[tuple[str, str]] = []
        for f in files:
            rows += entries(ROOT / f)
        if not rows:
            continue
        print(f"\n{BOLD}{title}:{NC}")
        if hint:
            print(f"  {GREY}{hint}{NC}")
        for target, desc in rows:
            print(f"  {GREEN}{BOLD}make {target:<22}{NC} {desc}")
    print()


if __name__ == "__main__":
    main()

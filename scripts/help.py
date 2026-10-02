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

SECTIONS: list[tuple[str, list[str]]] = [
    ("Основные команды", ["Makefile"]),
    ("Docker / контейнер", ["makefiles/docker.mk"]),
    ("Диагностика", ["makefiles/safety.mk"]),
    ("Симуляция Gazebo", ["makefiles/simulation.mk"]),
    ("Состояния робота", ["makefiles/controller.mk"]),
    ("Waypoint навигация", ["makefiles/navigation.mk"]),
    ("Эксперименты", ["makefiles/experiment.mk"]),
    ("YOLO", ["makefiles/yolo.mk"]),
    ("Elevation Mapping", ["makefiles/elevation.mk"]),
    ("Сборка и тесты", ["makefiles/rust.mk", "makefiles/test.mk"]),
    ("CI и линт", ["makefiles/ci.mk"]),
    ("NVIDIA", ["makefiles/nvidia.mk"]),
]

GREEN, BOLD, NC = "\033[0;32m", "\033[1m", "\033[0m"
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
    for title, files in SECTIONS:
        rows: list[tuple[str, str]] = []
        for f in files:
            rows += entries(ROOT / f)
        if not rows:
            continue
        print(f"\n{BOLD}{title}:{NC}")
        for target, desc in rows:
            print(f"  {GREEN}{BOLD}make {target:<22}{NC} {desc}")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
isaac_debug.py — единая система отладки для скриптов Isaac Sim.

Обеспечивает:
  - включение/отключение debug-вывода флагом --debug или env ISAAC_DEBUG
  - единый формат [tag] сообщений с flush=True (видно в логах headless)
  - цветовые маркеры: DEBUG (cyan), INFO (green), WARN (yellow), ERROR (red)
  - запись в файл лога (--log-file), если указан
  - счётчики/таймеры для замера частот (например, цикл публикации)

Использование:
    from isaac_debug import log, debug, info, warn, error, Timer, freq

    log.set_level("debug")           # debug|info|warn|error
    log.set_debug_env()              # читает ISAAC_DEBUG из env
    debug("импорт URDF", "начало")
    freq.tick("main_loop")           # замер частоты итераций
    print(freq.get("main_loop"))     # "12.3 Hz"
"""

import os
import sys
import time
from collections import defaultdict


class _Logger:
    """Простой логгер с уровнями и цветами (работает и без tty)."""

    LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40}

    _COLORS = {
        "debug": "\033[36m",   # cyan
        "info": "\033[32m",    # green
        "warn": "\033[33m",    # yellow
        "error": "\033[31m",   # red
        "reset": "\033[0m",
    }

    def __init__(self, level: str = "info"):
        self.level = self.LEVELS.get(level, 20)
        self._color_enabled = sys.stdout.isatty()

    def set_level(self, level: str) -> None:
        self.level = self.LEVELS.get(level, 20)

    def set_color(self, enabled: bool) -> None:
        self._color_enabled = enabled

    def set_debug_env(self) -> None:
        """Включает debug, если env ISAAC_DEBUG=1 (или --debug в argv)."""
        if os.environ.get("ISAAC_DEBUG") == "1":
            self.set_level("debug")
        if "--debug" in sys.argv:
            self.set_level("debug")

    def _emit(self, level: str, tag: str, msg: str) -> None:
        if self.LEVELS.get(level, 20) < self.level:
            return
        line = f"[{tag}] {msg}"
        if self._color_enabled:
            c = self._COLORS.get(level, "")
            line = f"{c}[{level.upper()}]{self._COLORS['reset']} {line}"
        # Всегда через оригинальный print (даже если print() перехвачен)
        _ORIGINAL_PRINT(line, flush=True)

    def debug(self, tag: str, msg: str) -> None:
        self._emit("debug", tag, msg)

    def info(self, tag: str, msg: str) -> None:
        self._emit("info", tag, msg)

    def warn(self, tag: str, msg: str) -> None:
        self._emit("warn", tag, msg)

    def error(self, tag: str, msg: str) -> None:
        self._emit("error", tag, msg)


# Совместимые псевдонимы функций
def debug(tag: str, msg: str) -> None:
    log.debug(tag, msg)


def info(tag: str, msg: str) -> None:
    log.info(tag, msg)


def warn(tag: str, msg: str) -> None:
    log.warn(tag, msg)


def error(tag: str, msg: str) -> None:
    log.error(tag, msg)


class _Freq:
    """Замер частоты вызовов по тегам (для главных циклов)."""

    def __init__(self, window: float = 2.0):
        self._counts = defaultdict(int)
        self._start = defaultdict(float)
        self._window = window
        self._last_rate = defaultdict(float)

    def tick(self, tag: str = "default") -> None:
        now = time.monotonic()
        if tag not in self._start:
            self._start[tag] = now
            self._counts[tag] = 0
        self._counts[tag] += 1
        dt = now - self._start[tag]
        if dt >= self._window:
            self._last_rate = {tag: self._counts[tag] / dt}
            self._counts[tag] = 0
            self._start[tag] = now

    def get(self, tag: str = "default") -> float:
        return self._last_rate.get(tag, 0.0)

    def report(self, tag: str = "default") -> str:
        return f"{self.get(tag):.1f} Hz"


class _Timer:
    """Замер времени выполнения фрагмента (для отладки медленных шагов)."""

    def __init__(self):
        self._t = time.monotonic()

    def reset(self) -> None:
        self._t = time.monotonic()

    def elapsed_ms(self) -> float:
        return (time.monotonic() - self._t) * 1000.0


# Глобальные экземпляры
log = _Logger()
freq = _Freq()
Timer = _Timer

# Оригинальный print (сохраняем, чтобы можно было восстановить)
_ORIGINAL_PRINT = print

_PRINT_TAG = "print"


def _patched_print(*args, **kwargs):
    """Замена print(): направляет сообщения в логгер.

    Аргументы print(...) конкатенируются (как в стандартном print),
    вывод идёт через log.info под тегом _PRINT_TAG. Это позволяет
    существующим файлам с print() получать отладочный вывод без
    переписывания каждой строки.
    """
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    msg = sep.join(str(a) for a in args)
    if end == "\n":
        log.info(_PRINT_TAG, msg)
    else:
        # print(..., end='') — без перевода строки: передаём как есть
        _ORIGINAL_PRINT(*args, **kwargs)


def redirect_print(enabled: bool = True, tag: str = "print") -> None:
    """Перенаправить print() в логгер (декларативно, для существующих файлов).

    Args:
        enabled: True — print() пишет в лог; False — вернуть стандартный print.
        tag: тег для сообщений от print.
    """
    global _PRINT_TAG
    _PRINT_TAG = tag
    if enabled:
        import builtins
        builtins.print = _patched_print
    else:
        import builtins
        builtins.print = _ORIGINAL_PRINT


def setup_debug() -> None:
    """Вызвать в начале main(): применит ISAAC_DEBUG / --debug.

    Декларативное использование:
        from isaac_debug import setup_debug, redirect_print, log
        setup_debug()
        redirect_print(tag="myapp")   # все print() → в лог
        log.info("myapp", "старт")
    """
    log.set_debug_env()
    # Если ISAAC_DEBUG=1 — автоматически включаем перенаправление print
    if os.environ.get("ISAAC_DEBUG") == "1":
        redirect_print()


def install(tag: str | None = None) -> None:
    """Одночстрокое декларативное подключение отладки.

    Делает: setup_debug() + (опционально) redirect_print(tag).

    Использование в любом скрипте Isaac:
        import isaac_debug; isaac_debug.install("myapp")

    Тогда: --debug / ISAAC_DEBUG=1 включают подробный вывод,
    а print() автоматически идёт в логгер под тегом "myapp".
    """
    setup_debug()
    if tag:
        redirect_print(tag=tag)


# --- Защита по памяти --------------------------------------------------

def available_memory_gb() -> float:
    """Вернуть доступную RAM в ГБ (из /proc/meminfo, MemAvailable).

    Работает на Linux; при ошибке возвращает inf (проверка пропускается).
    """
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    kb = int(line.split()[1])
                    return kb / (1024 * 1024)
    except Exception:
        pass
    return float("inf")


def require_memory(min_gb: float, tag: str = "memory", fatal: bool = True) -> bool:
    """Проверить, что доступной RAM >= min_gb перед запуском тяжёлого процесса.

    Isaac Sim headless потребляет ~11 GB. Если свободно меньше порога —
    процесс завершается с понятной ошибкой (вместо OOM-зависания).

    Args:
        min_gb: минимально требуемая доступная RAM в ГБ.
        tag: тег лога.
        fatal: True — exit() при нехватке; False — только warn и вернуть False.

    Returns:
        True — памяти достаточно (или проверка недоступна).
    """
    avail = available_memory_gb()
    if avail >= min_gb:
        log.info(tag, f"RAM OK: {avail:.1f} GB доступно (нужно >= {min_gb} GB)")
        return True
    msg = (
        f"RAM НЕДОСТАТОЧНО: {avail:.1f} GB доступно, нужно >= {min_gb} GB. "
        f"Закройте GUI-приложения (браузер, telegram, zed) или контейнеры "
        f"(elevation/gazebo). Запуск прерван, чтобы избежать OOM."
    )
    if fatal:
        log.error(tag, msg)
        sys.exit(1)
    log.warn(tag, msg)
    return False


# Авто-инициализация при импорте (если env уже задан)
if os.environ.get("ISAAC_DEBUG") == "1":
    log.set_level("debug")
    redirect_print()


if __name__ == "__main__":
    # Самопроверка
    log.set_level("debug")
    debug("test", "debug-сообщение")
    info("test", "info-сообщение")
    warn("test", "warn-сообщение")
    error("test", "error-сообщение")
    for _ in range(30):
        freq.tick("main")
    print("freq:", freq.report("main"))

    # Проверка redirect_print
    print("это print() — должен попасть в лог под тегом print")
    redirect_print(tag="myapp")
    print("это print() после redirect_print(tag='myapp')")
    redirect_print(enabled=False)
    print("это обычный print после отключения")

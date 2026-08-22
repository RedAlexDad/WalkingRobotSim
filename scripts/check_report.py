#!/usr/bin/env python3
"""
check_report.py — валидатор отчётов по формату troubleshooting-report.

Проверяет отчёт (Часть A + Часть B) на целостность, чтобы отловить
галлюцинации ИИ в нумерации и ссылках:

  1. Каждая ссылка [..](#якорь) ведёт на существующий заголовок
     или HTML-якорь (<a id="...">)
  2. Заголовки "## N. Проблема: ..." — сквозная нумерация без пропусков
     и дублей (имеется в виду нумерация, продолжающая Часть A)
  3. Каждая проблема имеет подразделы N.1..N.7
     (Симптом, Гипотезы, Причина, Диагностика, Решение,
      Исправление, Результат)
  4. Каждая гипотеза в N.2 помечена ✅ или ❌
  5. Каждая проблема имеет блок "Связь с развёртыванием (Часть A)"
  6. У каждой проблемы есть заголовок раздела в списке ссылок
     (не обязательно — информирует)

Использование:
    python3 scripts/check_report.py reports/isaam/2026-08-22_simulation-issues-report.md

Возврат: 0 — все проверки пройдены, 1 — найдены ошибки.
"""

import re
import sys


def slugify(text: str) -> str:
    """GitHub-алгоритм генерации якоря из заголовка."""
    # lowercase, убрать не-слово/пробел/дефис, пробелы -> дефисы
    t = text.strip().lower()
    t = re.sub(r"[^\w\s-]", "", t, flags=re.UNICODE)
    t = re.sub(r"\s+", "-", t)
    return t


def collect_headers(lines):
    """Собрать заголовки: (level, text, slug)."""
    headers = []
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            headers.append((level, text, slugify(text)))
    return headers


def collect_html_anchors(lines):
    """Собрать HTML-якоря <a id="...">.</a>."""
    ids = set()
    for line in lines:
        for m in re.finditer(r'<a id="([^"]+)"\s*/?>', line):
            ids.add(m.group(1))
    return ids


def collect_links(lines):
    """Собрать внутренние ссылки [..](#якорь)."""
    links = []
    for line in lines:
        for m in re.finditer(r"\]\(#([^)]+)\)", line):
            links.append(m.group(1))
    return links


def resolve_anchors(header_slugs, html_ids):
    """
    Построить множество доступных якорей.
    GitHub: при дублях заголовков второй получает суффикс -1, -2...
    """
    counts = {}
    available = set(html_ids)
    for slug in header_slugs:
        counts[slug] = counts.get(slug, 0) + 1
    for slug, n in counts.items():
        for i in range(n):
            available.add(slug if i == 0 else f"{slug}-{i}")
    return available


def find_problems(lines):
    """Найти заголовки '## N. Проблема: ...' -> (number, title, slug)."""
    problems = []
    for line in lines:
        m = re.match(r"^##\s+(\d+)\.\s+Проблема:\s+(.+)$", line)
        if m:
            problems.append((int(m.group(1)), m.group(2).strip(), slugify(f"{m.group(1)}. Проблема: {m.group(2)}")))
    return problems


def check_structure(lines, problems):
    """Для каждой проблемы проверить наличие N.1..N.7."""
    required_subsections = {
        "Симптом": "N.1",
        "Гипотезы": "N.2",
        "Причина": "N.3",
        "Диагностика": "N.4",
        "Решение": "N.5",
        "Исправление в скриптах/конфигах": "N.6",
        "Результат": "N.7",
    }
    errors = []
    for num, title, _ in problems:
        # Ищем диапазон: от заголовка проблемы до следующего
        # заголовка того же уровня (## ...)
        start_idx = None
        for i, line in enumerate(lines):
            if re.match(rf"^##\s+{num}\.\s+Проблема:", line):
                start_idx = i
                break
        end_idx = len(lines)
        for j in range(start_idx + 1, len(lines)):
            if re.match(r"^##\s+\d+\.\s+Проблема:", lines[j]):
                end_idx = j
                break
        block = lines[start_idx:end_idx]
        block_text = "\n".join(block)
        for subsection, label in required_subsections.items():
            expected = f"### {num}.{label.split('.')[1]}. {subsection}"
            if expected not in block_text:
                errors.append(f"Проблема {num}: отсутствует подраздел «{expected}»")

        # Проверка гипотез (только для N.2)
        if f"### {num}.2. Гипотезы" in block_text:
            hyp_start = None
            for i, line in enumerate(block):
                if re.match(rf"^###\s+{num}\.2\.\s+Гипотезы", line):
                    hyp_start = i
                    break
            hyp_end = len(block)
            for j in range(hyp_start + 1, len(block)):
                if re.match(rf"^###\s+{num}\.3\.", block[j]):
                    hyp_end = j
                    break
            hypotheses = [l for l in block[hyp_start:hyp_end] if re.match(r"^- .*Гипотеза", l)]
            for h in hypotheses:
                if "✅" not in h and "❌" not in h:
                    errors.append(f"Проблема {num}: гипотеза без вердикта ✅/❌: {h.strip()}")

        # Проверка блока «Связь с развёртыванием (Часть A)»
        if "Связь с развёртыванием (Часть A)" not in block_text:
            errors.append(f"Проблема {num}: отсутствует блок «Связь с развёртыванием (Часть A)»")
    return errors


def check_numbering(problems):
    """Проверить сквозную нумерацию проблем без пропусков/дублей."""
    errors = []
    numbers = [p[0] for p in problems]
    if len(set(numbers)) != len(numbers):
        errors.append("Дубли номеров проблем: " + str(numbers))
    if numbers and numbers != list(range(numbers[0], numbers[0] + len(numbers))):
        errors.append(f"Нумерация проблем не сквозная: {numbers}")
    return errors


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 scripts/check_report.py <отчёт.md> [<отчёт2.md> ...]")
        return 2

    total_fail = 0
    for path in sys.argv[1:]:
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print(f"[ERROR] {path}: {e}")
            total_fail += 1
            continue

        lines = text.splitlines()
        errors = []
        warns = []

        # 1. Ссылки
        headers = collect_headers(lines)
        html_ids = collect_html_anchors(lines)
        header_slugs = [h[2] for h in headers]
        available = resolve_anchors(header_slugs, html_ids)
        links = collect_links(lines)
        missing = [l for l in links if l not in available]
        for l in missing:
            errors.append(f"Ссылка ведёт на несуществующий якорь: #{l}")
        warns.append(f"ссылок={len(links)}, заголовков={len(headers)}, HTML-якорей={len(html_ids)}")

        # 2-5. Проблемы
        problems = find_problems(lines)
        errors += check_numbering(problems)
        errors += check_structure(lines, problems)

        # Вывод
        print(f"\n=== {path} ===")
        for w in warns:
            print(f"[INFO] {w}")
        if not problems:
            errors.append("В отчёте нет заголовков «## N. Проблема: ...» (Часть B отсутствует)")
        for e in errors:
            print(f"[FAIL] {e}")
        if not errors:
            print(f"[OK] Все проверки пройдены ({len(problems)} проблем, {len(links)} ссылок)")
        else:
            total_fail += 1

    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())

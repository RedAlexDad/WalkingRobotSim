# Исходные материалы для ИИАСУ-2026 (из `docs/ieee-article/`)

**Назначение:** что именно берём из папки PIERE и как переиспользуем.

---

## 1. Текст

| Источник | Как использовать |
|---|---|
| `docs/ieee-article/draft-article-en.md` | **источник истины** (v1.0, 3998 слов, 15 ссылок) |
| `docs/ieee-article/draft-article-ru.md` | база русского перевода; **синхронизировать** с EN |
| `docs/ieee-article/draft-article.md` | более ранний черновик (числа-заглушки) — не использовать |

Текст переводится/адаптируется, а не переписывается заново: структура
(Introduction, Architecture, Method, Experiments, Discussion, Conclusion)
сохраняется, формулировки — на русском.

## 2. Рисунки

| Файл | Подпись (черновая) |
|---|---|
| `figures/bw/fig_architecture.png` | архитектура системы (Rust → ROS 2 → IsaacLab → PhysX → Go2) |
| `figures/bw/fig_roll.png` | крен корпуса до/после правки дифференциальной длины |
| `figures/bw/fig_trajectory.png` | траектория в горизонтальной плоскости (IK vs RL) |
| `figures/bw/fig_speed.png` | достигнутая скорость vs командная (IK vs RL) |

Проверить требования шаблона (dpi, формат, подпись под рисунком).

## 3. Таблицы

| Файл | Содержание |
|---|---|
| `tables/table1_walking.xlsx` | прямое сравнение ходьбы (vx = 0.3 м/с) |
| `tables/table2_operating_range.xlsx` | рабочая область по скорости |
| `tables/table3_failure_modes.xlsx` | таксономия отказов IK |

> Шаблон допускает **≤2 таблицы** (≤20% объёма). Оставить/объединить две:
> например, «ходьба + рабочая область» и «таксономия отказов».

## 4. Данные

| Что | Где |
|---|---|
| Телеметрия (CSV/JSON) | `docs/ieee-article/telemetry/` |
| Отчёты | `reports/isaam/` |
| Код телеметрии/анализа | `src/isaac/telemetry.py`, `run_sim_telemetry.py`, `analyze_telemetry.py` |

Пересчёт чисел не требуется — все метрики уже в статье и таблицах.

## 5. Литература

- `docs/ieee-article/refs/references.md` — 15 ссылок с линками/DOI.
- Локальные копии 4 arXiv — в `docs/ieee-article/refs/`.
- При подаче в РИНЦ оформить по **ГОСТ**; проверить ID
  `arXiv:2607.18135`.

## 6. Куда кладём результат

- Готовую русскую статью — в эту папку (`docs/AI_ASU_2026/`) как
  `article-iiasu-ru.md` (или `.docx` по шаблону).
- Не изменять исходники в `docs/ieee-article/` — они нужны для REEPE 2027.

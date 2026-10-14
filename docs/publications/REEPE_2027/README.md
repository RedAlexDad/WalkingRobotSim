# REEPE 2027 / IEEE — рабочая папка по статье

**Конференция:** 9th International Youth Conference on Radio Electronics,
Electrical and Power Engineering (**REEPE 2027**), 07–09 апреля 2027
(IEEE Xplore / Scopus).
**Секция:** `Computing, Signal Processing, and Analysis`.
**Тема:** сравнение обученной политики и модельного IK/TROT-контроллера
для походки четвероногого робота (Unitree Go2) в Isaac Sim.
**Язык:** английский · **Шаблон:** IEEE · **Объём:** 5–6 страниц.

> Требования и шаблон PIERE-2026 (прошлая площадка) — в `../PIERE_2026/`.
> План подачи — `plan-reepe-2027.md`.

## Содержимое

| Файл / папка | Назначение |
| --- | --- |
| `plan-reepe-2027.md` | **план подачи в REEPE-2027** (секция, сроки, требования, чек-лист) |
| `draft-article.md` | черновик статьи (каркас) |
| `draft-article-en.md` | английская версия |
| `draft-article-ru.md` | русская версия (для сверки) |
| `data-collection.md` | досье данных: что проверено, чего не хватает |
| `improvement-plan.md` | план доводки статьи |
| `plan-final-experiments.md` | план финальных экспериментов |
| `VERSION-v1.0.md` | версия статьи |
| `generate_docx.py` | сборка `.docx` по шаблону |
| `figures/` | рисунки |
| `tables/` | таблицы |
| `telemetry/` | телеметрия (CSV/JSON) |
| `refs/` | локальные копии источников (arXiv + аннотации) |

## Быстрый порядок
1. `plan-reepe-2027.md` — секция, сроки, требования.
2. `data-collection.md` — свести данные RL vs IK/TROT.
3. `draft-article-en.md` — текст под IEEE (5–6 стр.).
4. `generate_docx.py` — собрать `.docx` по шаблону.

## Связанные материалы вне папки
- `../../gazebo-rl-vs-ik/`, `../../gpu-rl-training/` — RL/Go2.
- `reports/gazebo-rl/`, `reports/rl-sar/` — отчёты и данные.
- `sim/mjrl_go2/` — обучение и результаты.
- `../PIERE_2026/` — прошлые требования/шаблон PIERE.

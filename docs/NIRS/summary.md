## Goal
- Исправить формулы LaTeX в главах 3 НИРС для корректного отображения на GitHub (KaTeX)

## Constraints & Preferences
- Команды должны работать в KaTeX/GitHub
- Имена файлов и разделов должны сохраняться
- Коммиты должны быть атомарными

## Правила работы с библиографией
1. Для каждого списка литературы создать отдельный файл отслеживания верификации (`sources_verify.md`)
2. Искать/верифицировать источники по одному, записывая результаты в этот файл
3. Только когда ВСЕ источники текущего раздела верифицированы — массово внести правки в целевой файл (title.md)
4. Затем перейти к следующему файлу со списком литературы

## Progress
### Done
- **LaTeX fixes:** Заменены `\_` между `\mathrm{...}` на camelCase (10 паттернов в 5 файлах). AGENTS.md обновлён. Коммит `9901382`.
- **Intro paragraphs:** Добавлены вводные абзацы (≥5 предложений) во все 11 файлов главы 3.
- **Mermaid diagrams (ch3_02_architecture.md):** 3 диаграммы (архитектура, развёртывание, поток данных), конвертированы из X/Y-координат в `flowchart TB`.
- **Структурное сжатие подсекций (N → 3-4):**
  - `ch3_02_architecture.md`: 6 → 3 (3.2.1 архитектура+развёртывание, 3.2.2 коммуникации+TF, 3.2.3 поток данных+топики)
  - `ch3_03_docker.md`: 5 → 2 (3.3.1 сборка+запуск+сеть, 3.3.2 compose+make+отладка)
  - `ch3_04_lidar.md`: 7 → 3 (3.4.1 выбор+конвертер+PointCloud2, 3.4.2 TF-relay, 3.4.3 фильтры+валидация)
  - `ch3_05_tf_dds.md`: 7 → 3 (3.5.1 TF-дерево+релеи, 3.5.2 DDS+SHM+миграция, 3.5.3 QoS+выводы)
  - `ch3_06_filtering.md`: 7 → 4 (3.6.1 pipeline, 3.6.2 voxel+RAM+outlier, 3.6.3 visibility+body, 3.6.4 skip-frame+итог)
  - `ch3_07_ground_seg.md`: 6 → 3 (3.7.1 алгоритм GPF, 3.7.2 интеграция, 3.7.3 оптимизация+результаты)
  - `ch3_08_dem.md`: 8 → 4 (3.8.1 структура+слои, 3.8.2 pipeline GPU, 3.8.3 pipeline CPU, 3.8.4 визуализация+метрики)
  - `ch3_09_cost.md`: 9 → 4 (3.9.1 slope+roughness+elevationDiff, 3.9.2 traversability+пороги, 3.9.3 costmap+Nav2, 3.9.4 результаты)
  - `ch3_10_gait.md`: 8 → 4 (3.10.1 режимы traversability, 3.10.2 параметры+адаптация, 3.10.3 плавность+прогнозирование, 3.10.4 типы+валидация)
  - `ch3_11_testing.md`: 6 → 3 (3.11.1 сценарии+процедура, 3.11.2 результаты+таблица, 3.11.3 ошибки+уроки)
  - `ch3_12_metrics.md`: 8 → 4 (3.12.1 точность+производительность, 3.12.2 навигация, 3.12.3 инструменты+baseline, 3.12.4 целевые показатели)
  - `ch3_13_conclusions.md`: 5 → 3 (3.13.1 результаты+ТЗ+таблица, 3.13.2 проблемы, 3.13.3 развитие)
- **Bug fix (ch3_08_dem.md):** Восстановлены удалённые подсекции 3.8.4 и 3.8.5 после merge (перезаписаны соседним содержимым).
- **Confirmed DOIs (5 of 13)** для списка литературы гл.3:
  - Fankhauser grid_map (Springer 2016): `10.1007/978-3-319-26054-9_5`
  - Zermas GPF (ICRA 2017, а не IV): `10.1109/ICRA.2017.7989591`
  - Marder-Eppstein Office Marathon (ICRA 2010): `10.1109/ROBOT.2010.5509725`
  - Fankhauser CLAWAR 2014: `10.1142/9789814623353_0051`
  - Macenski Marathon 2 (IROS 2020): `10.1109/IROS45743.2020.9341207`
- **Confirmed URLs (3)**:
  - ROS 2 Jazzy: https://docs.ros.org/en/jazzy/
  - Cyclone DDS: https://cyclonedds.io/
  - Gazebo Harmonic: https://gazebosim.org/docs/harmonic

### In Progress
- **Поиск DOI для 3 источников** из списка гл.3 (см. `sources_verify_ch3.md`):
  - **#5** Fankhauser PhD thesis (ETH 2018) — не найден в Crossref; ETH handle `10.3929/ethz-b-000489726` тоже 404
  - **#11** Okada K. GPU-Accelerated Elevation Mapping (RA-L 2023) — не найден в Crossref по названию+автору
  - **#12** Wang C. Traversability Analysis (ICRA 2023) — не найден в Crossref по названию+автору

### Blocked
- IEEE Xplore возвращает login shell (JS-зависимая страница)
- Web search tool (parallel.ai) возвращает 403
- Google Scholar не индексирует точные названия из библиографии

## Next Steps
- Создать `sources_verify_ch3.md` для отслеживания верификации источников
- Для недостающих DOI: поискать на Semantic Scholar, ResearchGate, IEEE Xplore через API
- После верификации всех 13 источников — внести правки в `title.md`

## Relevant Files
- Все файлы `ch3_01_intro.md`–`ch3_13_conclusions.md` в `/home/redalexdad/GitHub/WalkingRobotSim/docs/NIRS/`
- `title.md` — целевой файл для вставки DOI/URL

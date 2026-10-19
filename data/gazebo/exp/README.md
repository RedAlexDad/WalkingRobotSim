# Бенчмарк YOLO в Gazebo

Полный бенчмарк пяти YOLO-моделей на сцене Gazebo: 16 объектов,
9 COCO-классов, 48 ракурсов, 88 объектов ground truth. Дополняет
ранний пилот из пяти стульев (история коммитов).

## Стенд

- Gazebo Sim 8.15.0, ROS 2 Jazzy, контейнер `walking_robot_sim`
  (`compose.yml`, сервис `simulator`), headless-рендер Ogre2.
- Камера: 640×480, HFOV 60°; позиция задаётся через
  `/world/exp/set_pose`.
- На каждый ракурс сохраняется один кадр — лучший из трёх по дисперсии:
  Gazebo иногда отдаёт пустой или недорисованный кадр.
- Сцена: 12 станций по кольцу радиусом 6.5 м, 16 объектов девяти
  COCO-классов: chair (2), dining table (3), bed (1), couch (2),
  vase (2), bottle (2), refrigerator (1), tv (1), sports ball (2).
- 48 ракурсов: 12 обзорных, 12 промежуточных, 12 крупных и 12 близких.
- Ground truth: проекция 3D-AABB объекта на кадр по известной позе
  камеры; обрезка по кадру, видимая площадь ≥ 35 %, минимум 8 px.
- Инференс: Ultralytics 8.4.182, PyTorch 2.13 CPU, 16-ядерный CPU,
  8 потоков torch; 50 прогонов, медиана. Кадры сняты в Gazebo,
  обработаны offline.

## Результаты

| Модель | T, мс | f, Гц | mAP@0.5 | mAP@0.5:0.95 | F1 max (conf) | Параметры, млн | Размер, МБ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| YOLOv8n | 20.4 | 49.0 | 0.403 | 0.260 | 0.479 (0.05) | 3.16 | 6.55 |
| YOLOv8s | 51.4 | 19.5 | 0.499 | 0.294 | 0.439 (0.05) | 11.17 | 22.59 |
| YOLOv10n | 19.5 | 51.4 | 0.427 | 0.278 | 0.345 (0.05) | 2.78 | 5.86 |
| YOLOv9t | 29.7 | 33.7 | 0.408 | 0.236 | 0.458 (0.05) | 2.13 | 4.97 |
| YOLO11n | 19.7 | 50.8 | 0.551 | 0.322 | 0.597 (0.05) | 2.62 | 5.61 |

`F1 max` — максимум по порогам 0.05…0.95 при IoU 0.5 и class-aware
сопоставлении. При фиксированном пороге 0.5 все модели показывают
низкий recall (0.02–0.17): уверенность на синтетических объектах
смещена вниз, рабочий порог нужно подбирать под домен.

### AP по классам (YOLO11n)

| Класс | AP@0.5 | AP@0.5:0.95 | Объектов |
| --- | --- | --- | --- |
| sports ball | 1.000 | 0.424 | 12 |
| tv | 0.976 | 0.829 | 6 |
| bottle | 0.838 | 0.358 | 8 |
| chair | 0.798 | 0.527 | 12 |
| bed | 0.464 | 0.126 | 4 |
| refrigerator | 0.461 | 0.346 | 6 |
| dining table | 0.280 | 0.234 | 18 |
| vase | 0.139 | 0.056 | 12 |
| couch | 0.000 | 0.000 | 10 |

PR-кривые по классам: `frames/pr_<model>.png`.

### Анализ ошибок

Confusion (GT → лучший предсказанный класс при IoU ≥ 0.5), YOLO11n:

- `tv` 6/6 и `sports ball` 8/12 (ещё 4 → `person`) — лучшие классы;
- `chair` 9/12 верно, 2 → `traffic light`, 1 пропуск;
- `dining table` 1/18: 6 → `bench`, 3 → `airplane`, 1 → `boat`,
  7 пропусков;
- `couch` 0/10: 6 → `bench`, 2 → `airplane`, 2 пропуска;
- `vase` 0/12: 2 → `bird`, 1 → `airplane`, 1 → `person`, 8 пропусков;
- `bed` 2/4 верно, 2 → `airplane`;
- `refrigerator` 2/6, ещё 1 → `tv`, 1 → `airplane`, 2 пропуска;
- `bottle` 5/8, 2 → `bird`, 1 → `person`.

Причина — доменный сдвиг: AWS-модели мебели в этой сцене почти белые,
без текстуры и интерьера. COCO-модели уверенно находят геометрию, но
относят её к неверным классам.

### Проверка на текстурированной сцене

Для контроля pipeline запущен на штатном `cafe.world` (текстурный
деревянный пол, стены, окна). YOLO11n на крупном плане даёт
`chair 0.902` и `car 0.901` (кадр `frames/cafe_sanity.png`). Это
подтверждает, что низкие метрики синтетической сцены связаны
с материалами/контекстом, а не с ошибкой оценки. Полный AP по кафе
не считался: GT тонких ножек и столешниц требует ручной разметки.

## Память и ROS-пайплайн

Пиковый RSS отдельного процесса (baseline torch+ultralytics — 529 МБ):

| Модель | Peak RSS, МБ | Δ к baseline, МБ |
| --- | --- | --- |
| YOLOv8n | 801.4 | 272.5 |
| YOLOv8s | 877.9 | 348.9 |
| YOLOv10n | 798.2 | 269.2 |
| YOLOv9t | 796.1 | 267.1 |
| YOLO11n | 797.4 | 268.4 |

RSS включает PyTorch и активации, а не только веса; для сравнения
моделей важнее Δ.

Штатный ROS-узел `quadropted_perception/yolo_detector` запущен в
контейнере после починки `torchvision` (0.29.1+cpu с CPU-индекса
PyTorch; PyPI-колесо не совпало по ABI с torch 2.14.1+cpu):

- камера 10 Гц → `/detections` 9.97 Гц (ограничение камеры);
- камера 60 Гц → камера 37.7 Гц, `/detections` 36.0 Гц
  (ограничение headless-рендеринга Gazebo, не инференса).

CSV-лог детекций: `/tmp/yolo_ros.csv`, `/tmp/yolo_ros_fast.csv`.

## Визуализация

- `frames/annotated/<model>/<view>.png` — bbox с классом и процентом
  уверенности; жёлтым показан ground truth.
- `frames/annotated_<model>_sheet.png` — контактный лист 48 ракурсов.
- `frames/pr_<model>.png` — PR-кривые по девяти классам.
- `frames/cafe_sanity.png` — пример на текстурированной сцене.

## Ограничения

- 88 GT-инстансов, у четырёх классов 4–8 объектов: AP по классу
  всё ещё грубый.
- GT — осевой 3D-AABB, а не ручная разметка; для повёрнутых объектов
  рамка консервативна.
- PBR-текстуры на простых примитивах в headless Ogre2 не рендерятся
  (чёрный материал), поэтому сцена собрана из готовых DAE-моделей.
- RSS включает PyTorch; чистая память модели — размер файла.
- Сквозной ROS-прогон ограничен рендерингом Gazebo (37.7 Гц камеры),
  а не инференсом.

## Воспроизведение

```bash
# 1. Собрать сцену и поднять Gazebo
.venv-lyrical/bin/python data/gazebo/exp/build_scene.py
docker compose exec -T simulator bash -lc \
  'pkill -x ruby; source /opt/ros/jazzy/setup.bash; \
   nohup gz sim -s -r /root/ws/data/exp/world.sdf > /tmp/gz.log 2>&1 &'

# 2. Снять 48 ракурсов
.venv-lyrical/bin/python data/gazebo/exp/capture_views.py

# 3. Бенчмарк и анализ (Gazebo лучше остановить — чище замер T)
docker compose exec -T simulator bash -lc 'pkill -x ruby'
.venv-lyrical/bin/python data/gazebo/exp/benchmark.py
.venv-lyrical/bin/python data/gazebo/exp/analyze.py
.venv-lyrical/bin/python data/gazebo/exp/sweep.py
.venv-lyrical/bin/python data/gazebo/exp/rss.py
```

Файлы: `build_scene.py`, `scene.json`, `world.sdf`, `capture.py`,
`capture_views.py`, `benchmark.py`, `analyze.py`, `sweep.py`, `rss.py`,
`benchmark_results.{json,csv}`, `confusion_*.json`, `sweep_*.json`,
`rss.json`.

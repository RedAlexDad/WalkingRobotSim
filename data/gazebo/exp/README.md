# Бенчмарк YOLO в Gazebo

Полноценный бенчмарк пяти YOLO-моделей на сцене Gazebo: 16 объектов,
9 COCO-классов, 24 ракурса, 44 объекта ground truth. Дополняет пилот
из пяти стульев (см. историю коммитов).

## Стенд

- Gazebo Sim 8.15.0, ROS 2 Jazzy, контейнер `walking_robot_sim`
  (`compose.yml`, сервис `simulator`), headless-рендер Ogre2.
- Камера: 640×480, HFOV 60°, 10 Гц; позиция задаётся через
  `/world/exp/set_pose`.
- Сцена: 12 станций по кольцу радиусом 6.5 м, 16 объектов девяти
  COCO-классов: chair (2), dining table (3), bed (1), couch (2),
  vase (2), bottle (2), refrigerator (1), tv (1), sports ball (2).
- 24 ракурса: 12 обзорных (по одному на станцию) и 12 промежуточных
  между станциями.
- Ground truth: проекция 3D-AABB объекта на кадр по известной позе
  камеры; обрезка по кадру, видимая площадь ≥ 35 %, минимум 8 px.
- Инференс: Ultralytics 8.4.182, PyTorch 2.13 CPU, 16-ядерный CPU,
  8 потоков torch; 50 прогонов, медиана. Кадры сняты в Gazebo,
  обработаны offline.

## Результаты

| Модель | T, мс | f, Гц | mAP@0.5 | mAP@0.5:0.95 | F1 max (conf) | Параметры, млн | Размер, МБ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| YOLOv8n | 19.8 | 50.6 | 0.375 | 0.242 | 0.429 (0.05) | 3.16 | 6.55 |
| YOLOv8s | 49.7 | 20.1 | 0.468 | 0.281 | 0.275 (0.05) | 11.17 | 22.59 |
| YOLOv10n | 20.1 | 49.8 | 0.401 | 0.286 | 0.333 (0.05) | 2.78 | 5.86 |
| YOLOv9t | 30.0 | 33.4 | 0.392 | 0.242 | 0.370 (0.05) | 2.13 | 4.97 |
| YOLO11n | 20.3 | 49.2 | 0.470 | 0.279 | 0.516 (0.05) | 2.62 | 5.61 |

`F1 max` — максимум по порогам 0.05…0.95 при IoU 0.5 и class-aware
сопоставлении. При фиксированном пороге 0.5 все модели показывают
низкий recall (0.00–0.14): уверенность на синтетических объектах
смещена вниз, рабочий порог нужно подбирать под домен.

### AP@0.5 по классам (YOLO11n)

| Класс | AP@0.5 | Объектов |
| --- | --- | --- |
| sports ball | 1.000 | 6 |
| tv | 0.917 | 3 |
| refrigerator | 0.667 | 3 |
| chair | 0.590 | 6 |
| bed | 0.556 | 3 |
| bottle | 0.500 | 2 |
| dining table | 0.000 | 9 |
| couch | 0.000 | 6 |
| vase | 0.000 | 6 |

### Анализ ошибок

Confusion (GT → лучший предсказанный класс при IoU ≥ 0.5), YOLO11n:

- `sports ball` 6/6 и `tv` 3/3 — распознаны верно;
- `chair` 3/6 верно, 2 → `traffic light`, 1 пропуск;
- `dining table` 0/9: 3 → `bench`, 3 → `airplane`, 1 → `boat`, 2 пропуска;
- `couch` 0/6: 3 → `bench`, 1 → `airplane`, 2 пропуска;
- `vase` 0/6: 2 → `bird`, 1 → `airplane`, 3 пропуска;
- `bed` 1/3 верно, 2 → `airplane`;
- `refrigerator` 1/3, ещё 1 → `tv`, 1 → `airplane`;
- `bottle` 1/2, 1 → `bird`.

Причина — доменный сдвиг: AWS-модели мебели в этой сцене почти белые,
без текстуры и интерьера. COCO-модели уверенно находят геометрию, но
относят её к неверным классам.

### Проверка на текстурированной сцене

Для контроля pipeline запущен на штатном `cafe.world` (текстурный
деревянный пол, стены, окна). YOLO11n на крупном плане даёт
`chair 0.902` и `car 0.901` (кадр `frames/cafe_sanity.png`). Это
подтверждает, что низкие метрики синтетической сцены связаны
с материалами/контекстом, а не с ошибкой оценки.

## Визуализация

- `frames/annotated/<model>/<view>.png` — bbox с классом и процентом
  уверенности; жёлтым показан ground truth.
- `frames/annotated_<model>_sheet.png` — контактный лист 24 ракурсов.
- `frames/cafe_sanity.png` — пример на текстурированной сцене.

## Ограничения

- 44 GT-инстанса, у части классов 1–3 объекта: AP по классу грубый.
- GT — осевой 3D-AABB, а не ручная разметка; для повёрнутых объектов
  рамка консервативна.
- PBR-текстуры на простых примитивах в headless Ogre2 не рендерятся
  (чёрный материал), поэтому сцена собрана из готовых DAE-моделей.
- Инференс выполнялся на хосте: в контейнере сломан `torchvision`,
  ROS-узел `yolo_detector` не запускался.
- Штатный `cafe.world` с камерой робота не поднимался: `launch_cpp`
  тянет GUI и полный Nav2.

## Воспроизведение

```bash
# 1. Собрать сцену и поднять Gazebo
.venv-lyrical/bin/python data/gazebo/exp/build_scene.py
docker compose exec -T simulator bash -lc \
  'pkill -x ruby; source /opt/ros/jazzy/setup.bash; \
   nohup gz sim -s -r /root/ws/data/exp/world.sdf > /tmp/gz.log 2>&1 &'

# 2. Снять 24 ракурса
.venv-lyrical/bin/python data/gazebo/exp/capture_views.py

# 3. Бенчмарк и анализ
.venv-lyrical/bin/python data/gazebo/exp/benchmark.py
.venv-lyrical/bin/python data/gazebo/exp/analyze.py
.venv-lyrical/bin/python data/gazebo/exp/sweep.py
```

Файлы: `build_scene.py`, `scene.json`, `world.sdf`, `capture.py`,
`capture_views.py`, `benchmark.py`, `analyze.py`, `sweep.py`,
`benchmark_results.{json,csv}`, `confusion_*.json`, `sweep_*.json`.

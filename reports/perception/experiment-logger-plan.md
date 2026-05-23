# План внедрения логгера экспериментов (время, дистанция, YOLO-детекции)

---

## 1. Мотивация

Для лабораторных работ требуется:
- Задать траекторию движения робота в файле, запустить, получить **время** и **пройденную дистанцию**
- Запустить YOLO-детектор и получить **лог распознанных объектов** с заданным интервалом (10/20/30 сек)
- Результаты должны сохраняться в файл для последующего анализа и оформления отчёта

---

## 2. Архитектура решения

```
┌──────────────────────────────────────────────────────────────┐
│                     gazebo_sim/scripts/                       │
│                                                              │
│  waypoint_collector.py        experiment_logger.py (NEW)     │
│  ┌─────────────────────┐     ┌──────────────────────────┐   │
│  │ /start_navigation   │     │ /start_experiment        │   │
│  │ /stop_navigation    │     │ /stop_experiment         │   │
│  │ /load_waypoints     │     │ subscribes: /robot1/odom │   │
│  │ ...                 │     │ logs: time, distance     │   │
│  └─────────────────────┘     └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  quadropted_perception/                       │
│                                                              │
│  yolo_detector.py (MODIFIED)                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ + log_interval_sec: 0/10/20/30                      │    │
│  │ + log_file: путь к файлу лога                       │    │
│  │ Таймер каждые N сек пишет детекции в файл            │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Компоненты

### 3.1 experiment_logger.py — новый узел

**Назначение:** замер времени прохождения маршрута и пройденной дистанции.

**Расположение:** `src/gazebo_sim/scripts/experiment_logger.py`

**Параметры:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `odom_topic` | string | `/robot1/odom` | Топик одометрии |
| `output_dir` | string | `/tmp/experiments` | Директория для логов |

**Сервисы:**

| Сервис | Тип | Описание |
|--------|-----|----------|
| `/start_experiment` | `std_srvs/Trigger` | Начать эксперимент: запомнить время+позицию |
| `/stop_experiment` | `std_srvs/Trigger` | Закончить: рассчитать метрики, записать в файл |

**Лог-файл** `experiment_<timestamp>.txt`:
```
=== Experiment Results ===
Start time: 2026-05-20 22:00:00
End time:   2026-05-20 22:01:30
Duration: 90.0 sec
Distance traveled: 12.5 m
Avg speed: 0.14 m/s
Waypoints: 7
Start position: (0.0, 0.0, 0.0)
End position:   (1.0, 0.5, 0.0)
--------------------------
Trajectory log (every ~1.0 sec):
t=0.0s   pos=(0.00, 0.00, 0.00)
t=1.0s   pos=(0.05, 0.02, 0.00)
...
```

**Алгоритм:**
1. Подписка на `/robot1/odom`, сохраняет последнюю позицию
2. `/start_experiment`: сбрасывает счётчики, записывает start_time, start_position
3. Каждую секунду (таймер) записывает текущую позицию в кольцевой буфер
4. `/stop_experiment` или авто-стоп при завершении навигации:
   - Вычисляет дистанцию (сумма евклидовых расстояний между точками трека)
   - Записывает результаты в файл
5. Интеграция с `waypoint_collector`: подписывается на `/start_navigation` для авто-старта

### 3.2 yolo_detector.py — модификация

**Новые параметры:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `log_interval_sec` | float | `0.0` | Интервал записи лога (0 = отключено) |
| `log_file` | string | `yolo_detections.log` | Путь к файлу лога |

**Лог-файл** (CSV-формат):
```
timestamp,class_id,class_name,confidence,center_x,center_y,width,height
22:00:05.000,0,person,0.87,320.5,240.1,120.3,250.2
22:00:05.000,56,chair,0.65,100.2,300.8,45.1,60.3
22:00:15.000,0,person,0.92,310.2,235.8,115.6,248.9
...
```

**Алгоритм:**
1. Таймер с интервалом `log_interval_sec`
2. При срабатывании: берёт последние детекции (сохраняются в `_last_detections`)
3. Пишет в файл: timestamp, класс, уверенность, bounding box
4. Если за интервал детекций не было — пишет пустую строку (marker)

### 3.3 Обновление waypoint_collector.py

**Изменения:**
- При старте навигации (`start_navigation_callback`) — публикует событие
- При завершении навигации — публикует событие
- Добавить топик `/navigation_status` (std_msgs/Bool) — для авто-останова логгера

---

## 4. Makefile цели

### Новый модуль: `makefiles/experiment.mk`

```makefile
## Запустить эксперимент: загрузить waypoints + старт навигации + логгирование
experiment-start:
	$(require-container)
	@docker exec $(CONTAINER_NAME) bash -c "... ros2 service call /start_experiment std_srvs/Trigger"

## Остановить эксперимент и сохранить результаты
experiment-stop:
	$(require-container)
	@docker exec $(CONTAINER_NAME) bash -c "... ros2 service call /stop_experiment std_srvs/Trigger"

## Показать путь к файлу с результатами
experiment-result:
	@echo "Results in: /tmp/experiments/ (inside container)"
	@echo "Copy to host: docker cp $(CONTAINER_NAME):/tmp/experiments ."
```

### Дополнение `makefiles/yolo.mk`

```makefile
## YOLO с логгированием в файл (пример: make yolo-log LOG_INTERVAL=10)
yolo-log:
	$(require-container)
	@docker exec -it $(CONTAINER_NAME) bash -c "... \
		ros2 run quadropted_perception yolo_detector \
		--ros-args -p log_interval_sec:=${LOG_INTERVAL} -p log_file:=/tmp/yolo_detections.log"
```

---

## 5. Этапы реализации

### Этап 1 — experiment_logger.py

- Создать файл `src/gazebo_sim/scripts/experiment_logger.py`
- Подписка на odom
- Сервисы start/stop
- Расчёт дистанции и времени
- Запись в файл
- Обновить `CMakeLists.txt` gazebo_sim для установки скрипта

### Этап 2 — Модификация yolo_detector.py

- Добавить параметры `log_interval_sec`, `log_file`
- Хранить последние детекции (`_last_detections`)
- Таймер для периодической записи
- CSV-формат лога

### Этап 3 — Makefile цели

- Создать `makefiles/experiment.mk`
- Подключить в `Makefile`
- Добавить `yolo-log` в `makefiles/yolo.mk`

### Этап 4 — Интеграция с launch-файлами

- Добавить experiment_logger в `gazebo_multi_nav2_world.launch.py`
- Добавить `yolo_log_interval` параметр в launch-файл YOLO

### Этап 5 — Обновление документации ЛР

- `exercise/lab1-waypoint.md`: добавить шаги с experiment_logger
- `exercise/lab2-yolo.md`: добавить шаги с yolo-log
- `exercise/common-errors-lab.md`: добавить типовые ошибки

---

## 6. Формат лог-файлов

### experiment_<timestamp>.txt
```
========================================
         EXPERIMENT RESULTS
========================================
Date:              2026-05-20 22:00:00
Duration:          90.5 sec
Distance traveled: 14.23 m
Average speed:     0.16 m/s
Waypoints:         7
Start position:    (0.00, 0.00, 0.00)
End position:      (1.02, 0.48, 0.00)
Status:            COMPLETED
========================================
```

### yolo_detections_<timestamp>.log
```
timestamp,class_id,class_name,confidence,center_x,center_y,width,height
2026-05-20_22:00:05.000,0,person,0.872,320.50,240.10,120.30,250.20
2026-05-20_22:00:05.000,56,chair,0.654,100.20,300.80,45.10,60.30
2026-05-20_22:00:15.000,0,person,0.915,310.20,235.80,115.60,248.90
2026-05-20_22:00:25.000,67,cell_phone,0.423,400.10,180.50,30.20,50.10
```

---

## 7. Зависимости

- **Новых пакетов не требуется** — всё есть в ROS 2 Jazzy
- `experiment_logger.py` использует: `rclpy`, `nav_msgs.msg.Odometry`, `std_srvs.srv.Trigger`
- `yolo_detector.py` changes: только стандартные библиотеки Python + уже существующие зависимости

---

## 8. Тестирование

### Модульное тестирование

```bash
# Проверка experiment_logger в изоляции
ros2 run gazebo_sim experiment_logger.py --ros-args -p odom_topic:=/robot1/odom

# Проверка YOLO с логгированием
ros2 run quadropted_perception yolo_detector \
    --ros-args -p log_interval_sec:=10 -p log_file:=/tmp/test_yolo.log
```

### Интеграционное тестирование

```bash
# 1. Запустить симуляцию
make gazebo-cpp

# 2. Загрузить маршрут
make waypoint-load FILE=my_route

# 3. Запустить эксперимент
make experiment-start
make waypoint-start

# 4. Дождаться завершения, проверить результат
make experiment-result
```

---

## 9. Makefile цели (итоговая сводка)

| Цель | Описание |
|------|----------|
| `experiment-start` | Запустить логгер эксперимента |
| `experiment-stop` | Остановить и сохранить результат |
| `experiment-result` | Показать путь к файлу с результатами |
| `yolo-detector` LOG_INTERVAL=10 | YOLO с логгированием каждые 10 сек |
| `waypoint-load FILE=...` | Загрузить маршрут (существующая) |
| `waypoint-start` | Запустить навигацию (существующая) |

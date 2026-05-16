# План внедрения YOLO для распознавания объектов

---

## 1. Архитектура

### Новая директория

```
src/quadropted_perception/
├── config/
│   └── yolo_detector.yaml         # Параметры детектора
├── launch/
│   └── yolo_detector.launch.py    # Launch файл
├── quadropted_perception/
│   ├── __init__.py
│   ├── yolo_detector.py           # ROS 2 node с инференсом
│   └── visualizer.py              # Визуализация детекций (RViz)
├── models/                        # Сюда класть локальные .pt файлы
│   └── .gitkeep
├── resource/
│   └── quadropted_perception
├── package.xml
├── setup.py
└── setup.cfg
```

### Поток данных

```
/gazebo/camera/image_raw
  │  [sensor_msgs/Image]
  ▼
yolo_detector.py
  │  (ultralytics YOLO, инференс)
  │  [quadropted_msgs/DetectionArray / vision_msgs/Detection2DArray]
  ▼
/detections
  │
  ▼
visualizer.py  ──→  RViz (маркеры/bbox)
```

---

## 2. Компоненты

### 2.1 yolo_detector.py

ROS 2 node на Python. Подписывается на топик камеры, публикует детекции.

**Параметры (YAML):**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `model_name` | string | `"yolov8n.pt"` | Название модели (скачается ultralytics или локальный путь) |
| `model_path` | string | `""` | Путь к локальной модели. Если указан — приоритет над model_name |
| `confidence_threshold` | float | `0.5` | Порог уверенности |
| `iou_threshold` | float | `0.45` | Порог NMS |
| `camera_topic` | string | `"/camera/image_raw"` | Входной топик изображения |
| `target_classes` | int[] | `[]` | Фильтр по классам (пусто — все) |
| `device` | string | `"cpu"` | `"cpu"` или `"cuda:0"` |
| `frame_id` | string | `"camera_link"` | Frame_id для детекций |

**Публикуемые топики:**

| Топик | Тип | Описание |
|-------|-----|----------|
| `/detections` | `quadropted_msgs/DetectionArray` | Массив найденных объектов |
| `/detected_image` | `sensor_msgs/Image` | Изображение с нарисованными bbox (для отладки) |

### 2.2 visualizer.py

Визуализация детекций в RViz через маркеры.

### 2.3 Сообщения (quadropted_msgs)

Добавить в quadropted_msgs:

```
# Detection.msg
int32 class_id
string class_name
float32 confidence
float64 center_x
float64 center_y
float64 width
float64 height

# DetectionArray.msg
std_msgs/Header header
Detection[] detections
```

---

## 3. Загрузка модели

Приоритет загрузки:

1. Если `model_path` не пустой — загрузить файл по указанному пути
2. Если `model_name` — загрузить через ultralytics (авто-скачивание) или из `models/`
3. Поиск модели сначала в папке `src/quadropted_perception/models/`, затем через ultralytics hub

Поддерживаемые форматы: `.pt` (PyTorch), `.onnx`, `.engine` (TensorRT).

---

## 4. Этапы реализации

### Этап 1 — Базовая структура

- Создать `src/quadropted_perception/` с package.xml, setup.py
- Определить сообщения Detection.msg, DetectionArray.msg
- Написать заглушку yolo_detector.py (подписка + публикация, без инференса)
- Проверить сборку: `colcon build`

### Этап 2 — Инференс

- Подключить ultralytics (добавить в package.xml зависимости)
- Реализовать загрузку модели (локальный файл или имя)
- Реализовать callback камеры: image → YOLO → detections
- Публикация `/detected_image` с bbox

### Этап 3 — Конфигурация и launch

- Создать `config/yolo_detector.yaml` с параметрами
- Создать `launch/yolo_detector.launch.py`
- Добавить make цель `make yolo` для запуска

### Этап 4 — Визуализация

- Реализовать visualizer.py (маркеры в RViz)
- Добавить конфиг RViz для отображения детекций

### Этап 5 — Интеграция с симуляцией

- Добавить камеру в модель робота (URDF/SDF), если ещё нет
- Настроить Gazebo камеру на роботе
- Проверить end-to-end: Gazebo → YOLO → RViz

---

## 5. Зависимости

- `ultralytics` (YOLOv8/v10/v11)
- `torch` (PyTorch)
- `opencv-python` (cv_bridge, отрисовка)
- `vision_msgs` (опционально, для стандартных сообщений)
- `sensor_msgs` (Image)
- `cv_bridge` (ROS Image ↔ OpenCV)

---

## 6. Makefile цель

```makefile
## Запуск YOLO детектора
yolo:
    @$(call require-container)
    @$(call exec, ros2 launch quadropted_perception yolo_detector.launch.py)
```

---

## 7. Docker

Добавить в Dockerfile:
- `ultralytics` + `torch` в stage `python-deps`
- Размер образа увеличится на ~2-3 GB (из-за torch)
- Опционально: использовать `torch --index-url https://download.pytorch.org/whl/cpu` для CPU-only

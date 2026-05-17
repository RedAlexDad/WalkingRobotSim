# YOLO Object Detection

Распознавание объектов через YOLO (Ultralytics) с камеры робота.

## Поток данных

```
Gazebo Camera ──→ /robot1/color/image_raw ──→ yolo_detector ──→ /detected_image
                                                         │
                                                         └──→ /detections ──→ visualizer ──→ RViz markers
```

## Запуск

### 1. Симуляция

```bash
make gazebo-py    # или make gazebo-cpp
```

### 2. YOLO детектор

```bash
make yolo-detector   # лог в терминал
```

### 3. Визуализация

```bash
make yolo-visualizer  # RViz split-screen
```

## Makefile цели

| Команда | Описание |
|---------|----------|
| `make yolo-detector` | YOLO инференс (лог в терминал) |
| `make yolo-visualizer` | visualizer + RViz split-screen |

## Параметры

Настройка в `config/yolo_detector.yaml`:

| Параметр | Дефолт | Описание |
|----------|--------|----------|
| `model_name` | `yolov8n.pt` | Модель YOLO |
| `model_path` | `""` | Путь к локальной модели |
| `confidence_threshold` | `0.5` | Порог уверенности |
| `iou_threshold` | `0.45` | Порог NMS |
| `camera_topic` | `/robot1/color/image_raw` | Топик камеры |
| `device` | `cpu` | `cpu` или `cuda:0` |

## Топики

| Топик | Тип | Описание |
|-------|-----|----------|
| `/robot1/color/image_raw` | `sensor_msgs/Image` | Вход: камера робота |
| `/detections` | `DetectionArray` | Результаты детекции |
| `/detected_image` | `sensor_msgs/Image` | Изображение с bbox |
| `/detection_markers` | `MarkerArray` | Маркеры для RViz |

## Модели в мире

В симуляции используются локальные модели:

| Модель | Описание |
|--------|----------|
| `chair` | Стул возле столика кафе |
| `mustard_bottle` | Горчица на столике |
| `prius_hybrid` | Машина на парковке |

## Docker

- `ultralytics` + `torch` (CPU-only) установлены в образе
- `numpy` зафиксирован `<2` из-за совместимости с cv_bridge
- `opencv-python` из pip удалён, используется системный `python3-opencv`

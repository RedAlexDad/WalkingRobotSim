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

### Этап 5 — Split-screen визуализация (raw camera + detected)

- Создать `rviz/yolo_detection.rviz` с двумя Image-дисплеями:
  - `Camera (raw)` — `/robot1/color/image_raw`
  - `Detected (bbox)` — `/detected_image`
- Также отображать маркеры детекций из visualizer (`/detection_markers`)
- Запуск через `make yolo-visualizer`:
  1. `yolo_detector` — инференс (bg, `make yolo`)
  2. `visualizer` — маркеры bbox (bg)
  3. `rviz2 -d yolo_detection.rviz` — GUI (foreground)

### Этап 6 — Разделение запуска: симуляция и YOLO

YOLO **не** встроен в launch-файлы симуляции. Запускается отдельно:

1. `make gazebo` / `make gazebo-py` — симуляция без YOLO
2. `make yolo-detector` — YOLO детектор (лог в терминал)
3. `make yolo-visualizer` — visualizer + RViz split-screen

Это снижает нагрузку на CPU при старте и даёт гибкость: можно запускать YOLO
только когда нужно распознавание, без перезапуска симуляции.

---

## 5. Зависимости

- `ultralytics` (YOLOv8/v10/v11)
- `torch` (PyTorch)
- `opencv-python` (cv_bridge, отрисовка)
- `vision_msgs` (опционально, для стандартных сообщений)
- `sensor_msgs` (Image)
- `cv_bridge` (ROS Image ↔ OpenCV)

---

## 6. Makefile цели

### `make yolo-detector` — запуск YOLO детектора (лог в терминал)

```makefile
yolo-detector:
	$(require-container)
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception yolo_detector"
```

### `make yolo-visualizer` — RViz split-screen + маркеры

```makefile
yolo-visualizer:
	$(require-container)
	$(check-x11)
	@docker exec -d $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception visualizer"
	@sleep 1
	@docker exec -d $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		rviz2 -d /root/ws/src/quadropted_perception/rviz/yolo_detection.rviz"
```

Экран разделён на две части:
- **Слева:** сырое изображение с камеры (`/robot1/color/image_raw`)
- **Справа:** изображение с нарисованными bbox (`/detected_image`)
- **Маркеры:** bbox и подписи в 3D-сцене (`/detection_markers`)

---

## 7. Docker

Добавить в Dockerfile:
- `ultralytics` + `torch` в stage `python-deps`
- Размер образа увеличится на ~2-3 GB (из-за torch)
- Использовать `torch --index-url https://download.pytorch.org/whl/cpu` для CPU-only

---

## 8. Отладка и устранение проблем

### 8.1 setup.py — entry_points

**Проблема:** `ros2 run quadropted_perception yolo_detector` не находил исполняемый файл.

**Причина:** в `setup.py` отсутствовал `entry_points`, из-за чего `colcon` не регистрировал исполняемые файлы.

**Решение:** добавлен `entry_points` в `setup.py`:
```python
entry_points={
    "console_scripts": [
        "yolo_detector = quadropted_perception.yolo_detector:main",
        "visualizer = quadropted_perception.visualizer:main",
    ],
}
```

---

### 8.2 CMakeLists.txt — установка .py вместо исполняемых файлов

**Проблема:** `ros2 run` требовал файлы без расширения `.py` в `lib/package/`.

**Причина:** `CMakeLists.txt` устанавливал `.py` файлы через `install(PROGRAMS ...)`. ROS 2 ищет исполняемые файлы по имени без расширения.

**Решение:** созданы wrapper-скрипты в `scripts/yolo_detector` и `scripts/visualizer`:
```python
#!/usr/bin/env python3
from quadropted_perception.yolo_detector import main
main()
```
Установка через `install(PROGRAMS scripts/yolo_detector scripts/visualizer DESTINATION lib/${PROJECT_NAME})`.

---

### 8.3 Неверный топик камеры

**Проблема:** YOLO подписывался на `/camera/image_raw` (дефолт), а симуляция публикует на `/robot1/color/image_raw`.

**Решение:**
- `config/yolo_detector.yaml`: `camera_topic: "/robot1/color/image_raw"`
- `launch/yolo_detector.launch.py`: дефолт изменён
- `yolo_detector.py`: дефолт параметра изменён на `/robot1/color/image_raw`

---

### 8.4 Numpy 2.x — несовместимость с cv_bridge

**Проблема:** `cv_bridge` собран с numpy 1.x, но `ultralytics` тянет numpy 2.x.

**Ошибка:**
```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.4.5
```

**Решение:** принудительная установка numpy<2 в Dockerfile:
```dockerfile
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed 'numpy<2'
```

Также pinned в секции python-deps: `numpy` → `'numpy<2'`.

После правки запускать даунгрейд вручную в контейнере:
```bash
pip install --break-system-packages 'numpy<2'
```

---

### 8.5 opencv-python из pip сломал систему OpenCV

**Проблема:** `ultralytics` установил `opencv-python` 4.13.0 (требует numpy>=2), который переопределил системный `python3-opencv` 4.6.0 (совместим с numpy 1.x). После даунгрейда numpy OpenCV перестал импортироваться.

**Решение:** удалён `opencv-python` из pip, используется системный `python3-opencv`:
```bash
pip uninstall opencv-python -y --break-system-packages
```

В Dockerfile добавлен шаг удаления `opencv-python` после установки ultralytics:
```dockerfile
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed ultralytics \
    && pip3 uninstall --break-system-packages -y opencv-python
```

---

### 8.6 Torch CUDA vs CPU — torchvision несовместимость

**Проблема:** `torchvision` 0.27.0 был установлен с CUDA-версией torch, но после переустановки CPU-only torch остался CUDA-совместимый torchvision.

**Ошибка:**
```
RuntimeError: operator torchvision::nms does not exist
```

**Решение:** переустановка torch и torchvision с CPU-индекса PyTorch:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    --break-system-packages --ignore-installed
```

---

### 8.7 Пустой header у /detected_image

**Проблема:** в RViz топик `/detected_image` показывал "no image".

**Причина:** `cv2_to_imgmsg()` создаёт Image без header (stamp=0, frame_id="").

**Решение:** копировать header из исходного сообщения камеры:
```python
debug_msg = self._bridge.cv2_to_imgmsg(annotated, encoding="bgr8")
debug_msg.header = msg.header  # копируем timestamp и frame_id
self._pub_debug_image.publish(debug_msg)
```

---

### 8.8 YAML параметр target_classes вызывал ParameterUninitializedException

**Проблема:** при старте через `ros2 launch` с `--params-file` параметр `target_classes: []` в YAML создавался как пустой массив, что конфликтовало с `declare_parameter("target_classes", [])` в коде.

**Решение:** удалён `target_classes` из YAML-конфига, т.к. код объявляет его с дефолтом `[]`.

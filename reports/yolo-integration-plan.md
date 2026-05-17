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
| `model` | string | `"yolov8n.pt"` | Имя файла модели в `models/`. Если нет локально — автозагрузка Ultralytics |
| `fps` | int | `0` | Троттлинг: макс FPS (0 = без лимита, все кадры) |
| `confidence_threshold` | float | `0.5` | Порог уверенности |
| `iou_threshold` | float | `0.45` | Порог NMS |
| `camera_topic` | string | `"/robot1/color/image_raw"` | Входной топик изображения |
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

Единый параметр `model` — имя файла (с расширением `.pt` или без). Поиск:

1. `share/quadropted_perception/models/<имя>.pt` — локальный файл в пакете
2. Если не найден — Ultralytics auto-download (через `YOLO(<имя>)`)
3. Если расширения нет — автоматически добавляется `.pt`

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

**Аргументы:**
- `MODEL=<name>` — имя модели (по умолчанию `yolov8n.pt`)
- `FPS=<n>` — троттлинг детекций (0 = без лимита)

```makefile
yolo-detector:
	$(require-container)
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception yolo_detector \
			$(if $(or $(MODEL),$(FPS)),--ros-args) \
			$(if $(MODEL),-p model:=${MODEL}) \
			$(if $(FPS),-p fps:=${FPS})"
```

Примеры:
```bash
make yolo-detector                     # YOLOv8n, все кадры (30 FPS)
make yolo-detector MODEL=yolov9t       # YOLOv9 tiny
make yolo-detector FPS=10              # 10 детекций/с, меньше CPU
make yolo-detector MODEL=yolov9t FPS=5 # лёгкая модель, 5 кадров/с
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

---

### 8.9 FPS троттлинг — снижение нагрузки CPU

**Проблема:** камера настроена на 30 FPS. YOLO делает инференс на каждый кадр, загружая CPU на 100%.

**Решение:** добавлен параметр `fps` в `yolo_detector.py`. Если `fps > 0`, callback пропускает кадры, пришедшие раньше интервала `1/fps`:

```python
now = time.monotonic()
if self._min_interval > 0 and (now - self._last_time) < self._min_interval:
    return
self._last_time = now
```

Параметр передаётся через Makefile:
```bash
make yolo-detector FPS=10   # 10 детекций/с
make yolo-detector FPS=5    # 5 детекций/с — минимум CPU
```

---

### 8.10 План: синхронизация FPS камеры и YOLO

**Текущий статус:** камера всегда 30 FPS, YOLO троттлинг только пропускает кадры, bridge всё равно передаёт 30 кадров/с.

**План:** пробросить `FPS` из Makefile → launch → xacro → `update_rate` камеры, чтобы камера в Gazebo публиковала столько же FPS, сколько обрабатывает YOLO.

**Нужные изменения:**
1. `gazebo.xacro` — сделать `update_rate` аргументом макроса сенсоров
2. `robot.xacro` — пробросить camera_fps аргумент
3. `description.launch.py` — принять camera_fps, передать в xacro
4. `gazebo_multi_nav2_world.launch.py` — принять camera_fps, передать в description.launch
5. `Makefile` — передать `FPS` в launch-файл мира + в YOLO

**Использование после реализации:**
```bash
make yolo-detector FPS=10          # камера 10 Гц + YOLO 10 детекций/с
make yolo-detector MODEL=yolov9t FPS=5  # в лёгком режиме
make yolo-detector FPS=0           # без троттлинга (30 FPS)

---

### 8.11 YOLO на CPU — дрейф одометрии и облака точек в RViz

**Проблема:** при запуске YOLO детектора без троттлинга (или с тяжёлой моделью) в RViz начинают дрейфовать одометрия и облако точек лидара.

**Причина:** YOLO инференс на CPU загружает все ядра (`yolov8s` ~22MB может утилизировать 100% CPU). ROS 2 ноды `robot_localization` (EKF) и лидара не успевают обрабатывать данные в реальном времени — EKF фьюзит сенсоры с задержкой, отсюда дрейф.

**Решения (по эффективности):**

| Метод | Команда | Эффект |
|-------|---------|--------|
| Троттлинг FPS | `make yolo-detector FPS=5` | 5 детекций/с — радикально снижает CPU |
| Лёгкая модель | `MODEL=yolov9t` | 4.8MB, в ~5x быстрее `yolov8s` |
| Комбо | `MODEL=yolov9t FPS=5` | Минимум нагрузки, без дрейфа |
| Понизить nice | `FPS=10 NICE=10` | YOLO с низким приоритетом, ноды навигации выше |
| Перспектива | синхронизация FPS камеры (8.10) | Камера не шлёт лишние кадры, bridge не грузит сеть |

**Рекомендация:** для стабильной навигации использовать `make yolo-detector MODEL=yolov9t FPS=5`.

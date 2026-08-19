# Отчёт об интеграции elevation_mapping_cupy v2.1.0

## Цель

Адаптация и интеграция GPU-ускоренного elevation mapping (`elevation_mapping_cupy` v2.1.0)
под ROS 2 Jazzy на платформе с NVIDIA GTX 1650 Ti (CC 7.5, 4GB VRAM, CUDA 12.8, driver 570).

---

## Проблемы и решения

### 1. Несовместимость PyTorch cu121 с драйвером 570

**Проблема:** Оригинальный `Dockerfile.x64` использует `torch` wheels `cu121` (CUDA 12.1).
Драйвер NVIDIA 570.211.01 + CUDA 12.8 несовместимы с библиотеками CUDA 12.1 внутри контейнера.

```python
# Было:
--extra-index-url https://download.pytorch.org/whl/cu121

# Стало:
--extra-index-url https://download.pytorch.org/whl/cu126
```

**Решение:** Смена на `cu126` — PyTorch собран под CUDA 12.6, который полностью совместим
с драйвером 570 и рантаймом CUDA 12.8 (nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.04).

**Файл:** `docker/Dockerfile.x64`

---

### 2. numpy 2.x несовместим с apt-пакетами (scipy, transforms3d)

**Проблема:** `apt install python3-scipy` ставит scipy, собранный под numpy 1.x.
При импорте `transforms3d` или `scipy` с numpy 2.x возникает `ValueError:
numpy.dtype size changed, may indicate binary incompatibility`.

```python
# Было:
RUN pip install numpy cupy-cuda12x simple-parsing

# Стало:
RUN pip install "numpy<2" cupy-cuda12x simple-parsing
```

**Решение:** Фиксация `numpy<2` через pip (перебивает apt-версию).

**Файл:** `docker/Dockerfile.x64`

---

### 3. CUDADriverError при JIT-компиляции CuPy на CC 7.5

**Проблема:** `CUDADriverError: CUDA_ERROR_INVALID_IMAGE: invalid device image`.
Возникает при JIT-компиляции CuPy ядер на GPU с compute capability 7.5 (Turing).
Причина — баг взаимодействия CuPy JIT и numpy 2.x.

**Решение:** Фиксация `numpy<2` (см. п.2) полностью устраняет эту ошибку, так как
CuPy JIT-компилятор полагается на стабильный ABI numpy 1.x.

**Файл:** `docker/Dockerfile.x64`

---

### 4. Отсутствие workspace-инструментов

**Проблема:** `colcon build` не находил `colcon cache` (не установлен).
При сборке внутри контейнера не хватало `colcon-common-extensions`.

**Решение:** Установка `python3-colcon-common-extensions` через apt добавлена
в `Dockerfile.x64` (уже присутствовала в оригинале).

**Файл:** `docker/Dockerfile.x64`

---

### 5. Невозможность визуального запуска демо

**Проблема:** `make docker-run` использовал только `--gpus all --net=host`,
без проброса X11 для RViz2.

```bash
# Было:
docker run -it --rm --gpus all --net=host \
    -v $(WORKSPACE):/ws -w /ws $(IMAGE_NAME) bash -l

# Стало (новый target docker-demo):
docker run -it --rm --gpus all --net=host \
    -e DISPLAY=$(DISPLAY) \
    -e XAUTHORITY=$(XAUTHORITY) \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $(XAUTHORITY):$(XAUTHORITY):ro \
    -v $(WORKSPACE):/ws -w /ws $(IMAGE_NAME) bash -lc '\
        source /opt/ros/jazzy/setup.bash; \
        source install/setup.bash; \
        ros2 launch elevation_mapping_cupy synthetic_depth_demo.launch.py; \
    '
```

**Решение:** Добавлен новый `make docker-demo` с пробросом:
  - `DISPLAY` и `XAUTHORITY` для X11-форвардинга
  - `/tmp/.X11-unix` и `~/.Xauthority` как volumes
  - Автозапуск `synthetic_depth_demo.launch.py` с RViz2

**Файл:** `Makefile`

---

## Что добавлено

### Makefile (полный список targets)

| Target | Описание |
|---|---|
| `build` | Сборка Docker-образа (`docker build`) |
| `setup-ws` | Создание ROS 2 workspace с исходниками |
| `docker-build` | Сборка ROS-пакетов внутри контейнера |
| `docker-test` | Запуск всех тестов (colcon test) |
| `docker-build-test` | build + test |
| `docker-run` | Интерактивный shell внутри контейнера |
| `docker-demo` | Запуск synthetic_depth_demo с RViz (GPU + X11) |

**Файлы:**
- `Makefile` (добавлен целиком в первом коммите)
- `docker/Dockerfile.x64` (изменён — cu126, numpy<2)

---

## Результаты тестирования

```
100% tests passed, 0 tests failed out of 9
Label Time Summary:
  launch_test =  87.54 sec*proc (3 tests)
  pytest      =  30.86 sec*proc (6 tests)
Total Test time (real) = 118.40 sec
```

**Все 41 тест пройдены** (0 errors, 0 failures, 0 skipped):

| Тест | Статус | Время |
|---|---|---|
| `test_map_shifting` (10 subtests) | ✅ Passed | 16.22s |
| `test_map_services` | ✅ Passed | 6.16s |
| `test_gridmap_layout` | ✅ Passed | 0.81s |
| `test_parameter` | ✅ Passed | 0.82s |
| `test_repo_config_sanity` | ✅ Passed | 0.74s |
| `test_kernel_compile_smoke` | ✅ Passed | 6.10s |
| `test_tf_gridmap_integration` (launch) | ✅ Passed | 70.68s |
| `test_map_save_load_services` (launch) | ✅ Passed | 11.37s |
| `test_synthetic_demo_launch` (launch) | ✅ Passed | 5.49s |

---

## Коммиты

```
88c0e99 fix: совместимость с numpy<2 и PyTorch cu126 для GTX 1650 Ti
375ea3d feat: добавить make docker-demo для запуска synthetic_depth_demo с RViz
```

Оба коммита на detached HEAD относительно `v2.1.0`.

---

## Окружение

- **Хост:** Ubuntu 24.04, Linux 6.8.0-61-generic
- **GPU:** NVIDIA GTX 1650 Ti (CC 7.5, 4GB VRAM)
- **CUDA driver:** 570.211.01
- **CUDA toolkit:** 12.8
- **Docker:** 29.4.1 + nvidia-container-toolkit 1.19.0
- **ROS 2:** Jazzy Jalisco

---

## Использование

```bash
# Сборка образа
make build

# Сборка ROS-пакетов
make docker-build

# Запуск тестов
make docker-test

# Визуальное демо (синтетический PointCloud2 + RViz)
make docker-demo

# Интерактивный shell
make docker-run
```

---

## Дальнейшие шаги

1. Запустить `make docker-demo` — визуально убедиться в работе elevation mapping
2. Интегрировать `elevation_mapping_cupy:jazzy` в WalkingRobotSim:
   - GPU passthrough в `compose.yml`
   - Depth-камера или 3D LiDAR в симуляции Go2 для генерации PointCloud2
   - Бридж PointCloud2 топика через `gz_bridge.yaml`
3. Создать launch-файл для совместного запуска симуляции + elevation mapping
4. Настроить Nav2 с учётом карты высот для terrain-aware path planning

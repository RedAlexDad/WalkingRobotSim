# Report 2026-06-27 15:48:23 MSK

**Branch:** feat/elevation-mapping
**Stats:** 4 files changed, 49 insertions(+), 6 deletions(-) (+ .last_elevation_build_commit)

## Что было добавлено

- **`makefiles/nvidia.mk`** — новый makefile с проверкой и установкой nvidia-container-toolkit:
  - `nvidia-check` — проверяет наличие `nvidia-ctk` и настройку `nvidia` runtime в Docker
  - `nvidia-install` — устанавливает nvidia-container-toolkit (ключи GPG, apt, настройка Docker)
  - `require-nvidia-toolkit` — функция для использования в качестве зависимости других целей
- **`install_nvidia_container_toolkit.txt`** — текстовый файл с командами установки (для копирования)

## Что было изменено

1. **`elevation_mapping_cupy/docker/Dockerfile.x64`** (2 коммита):

   - **CUDA 12.6 → 12.8**: Базовый образ обновлён с `nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.04` до `nvidia/cuda:12.8.0-cudnn-devel-ubuntu24.04`. Причина — CUDA 12.6 не поддерживает Blackwell (sm_120), необходимый для RTX 5070 Ti.
   - **CuPy из исходников**: `cupy-cuda12x` (предсобранный wheel) заменён на `cupy --no-binary cupy` с `CUPY_NVCC_GENCODE="arch=compute_120,code=sm_120"`. Предсобранные wheel'ы `cupy-cuda12x` не содержат бинарников для sm_120 и не имеют sdist на PyPI.
   - **PyTorch**: Индекс установки изменён с `cu126` на `cu128` для совместимости с CUDA 12.8.

2. **`Makefile`**:
   - Добавлен `include makefiles/nvidia.mk`

3. **`makefiles/elevation.mk`**:
   - Цели `elevation`, `elevation-bg`, `elevation-build`, `elevation-force-build` теперь зависят от `nvidia-check`

## Проблемы

### 1. Сеть: IPv6 недоступен
При первой попытке сборки Docker не мог достучаться до `registry-1.docker.io` через IPv6 — `network is unreachable`.
**Решение**: Настроен приоритет IPv4.

### 2. nvidia-container-toolkit не установлен
`could not select device driver "nvidia" with capabilities: [[gpu]]` — драйвер NVIDIA в Docker отсутствовал.
**Решение**: Установлен `nvidia-container-toolkit` через apt и настроен runtime Docker.

### 3. CuPy: CUDA_ERROR_NO_BINARY_FOR_GPU
Три итерации исправления:
- **Попытка 1**: `CUPY_NVCC_GENCODE` с `cupy-cuda12x --no-binary cupy-cuda12x` — пакет `cupy-cuda12x` не имеет sdist на PyPI, pip не может собрать из исходников.
- **Попытка 2**: `CUPY_NVCC_GENCODE` с `cupy --no-binary cupy` — CuPy собрался из исходников, но NVCC 12.6 не поддерживает sm_120 (`nvcc fatal: Value 'sm_120' is not defined`). CUDA 12.6 поддерживает максимум sm_90 (Hopper).
- **Попытка 3 (успех)**: Обновление базового образа до CUDA 12.8.0, в которой добавлена поддержка Blackwell (sm_120). CuPy собран из исходников под sm_120.

### 4. Медленная сеть при скачивании образов
Образ `nvidia/cuda:12.8.0-cudnn-devel` весит ~6 GB, скачивание шло долго.

### 5. RViz: Ошибки загрузки mesh-файлов Go2
```
Could not load resource file:///root/ws/install/go2_description/.../hip.dae
```
Mesh-файлы робота Go2 не смонтированы в контейнер elevation. Ворнинг не влияет на работу ноды картографии.

### 6. RViz: GLSL warning
```
active samplers with a different type refer to the same texture image unit
```
Косметическая проблема RViz, не влияет на функциональность.

## Как были решены

| Проблема | Решение |
|----------|---------|
| Нет nvidia-container-toolkit | `makefiles/nvidia.mk` + `make nvidia-install` |
| CUDA 12.6 не поддерживает RTX 5070 Ti | Обновлён до CUDA 12.8.0 |
| CuPy нет sm_120 в wheels | Сборка CuPy из исходников с `CUPY_NVCC_GENCODE=sm_120` |
| Нет автоматической проверки перед запуском | `nvidia-check` как зависимость `elevation`-целей |

## Итоговый статус

**`make elevation` — работает.**

- CUDA 12.8.0, CuPy 13.6.0
- Карта высот инициализирована: 20×20 м, разрешение 0.1 м, 200×200 ячеек
- Поступают слои: elevation, variance, traversability, slope, roughness, cost
- Все плагины загружены: min_filter, smooth_filter, inpainting, surface_gradient, roughness, cost_function, erosion

## Что нужно учитывать в будущем

- **Поддержка новых GPU**: При смене видеокарты может потребоваться обновление версии CUDA в Dockerfile и CUPY_NVCC_GENCODE. Для новых архитектур NVIDIA может потребоваться не только предсобранный wheel, но и сборка CuPy из исходников.
- **Mesh-файлы Go2**: Если нужна корректная визуализация робота в RViz, нужно смонтировать `go2_description` в контейнер elevation_mapping.
- **Размер образов**: cudnn-devel образы очень большие. При ограниченном интернете можно использовать `-devel` без `-cudnn`, если cuDNN не требуется.
- **Кеш Docker**: При изменениях в Dockerfile может потребоваться `docker builder prune` или ручное удаление слоёв, если `make elevation-force-build` не пересобирает из-за кеша.

# Установка и запуск NVIDIA Isaac Sim 6.0.1.0

## Quadruped Robot Simulator — WalkingRobotSim (НИР, ВКРМ)

### Дата: 2026-07-18 (вечерняя сессия)

### Автор: Папин А. В., ИУ5, ИВТ, МАГИСТРАТУРА

---

## 1. Executive Summary

**Цель сессии:** Установить NVIDIA Isaac Sim 6.0.1.0 на хост-ОС (Ubuntu 24.04.4) в изолированном Python venv, запустить GUI-симулятор на RTX 5070 Ti (eGPU OCuLink) и подготовить интеграцию с существующим ROS2-стеком WalkingRobotSim.

**Результат:** Isaac Sim успешно установлен, запущен в полноэкранном GUI-режиме, все 200+ расширений загружены, ROS2 bridge автоматически инициализирован, GPU RTX 5070 Ti корректно определена. Создан `.desktop` файл для запуска из системного меню.

---

## 2. Исходные данные

### 2.1 Система

| Параметр            | Значение                                                     |
| ------------------- | ------------------------------------------------------------ |
| **OS**              | Ubuntu 24.04.4 LTS (Noble Numbat)                            |
| **CPU**             | AMD Ryzen 7 H 255 w/ Radeon 780M Graphics (8C/16T)           |
| **GPU**             | NVIDIA GeForce RTX 5070 Ti (Blackwell sm_120, 16303 MB VRAM) |
| **GPU (iGPU)**      | AMD Radeon 780M Graphics (RADV Phoenix)                      |
| **Driver**          | NVIDIA 595.71.05                                             |
| **CUDA**            | nvcc 12.8.93 (host), CUDA Toolkit 12.9 (runtime)             |
| **RAM**             | 30 GB                                                        |
| **Docker**          | 29.4.0, nvidia-container-toolkit 1.19.1                      |
| **Python**          | 3.12.3 (system), 3.12.3 (venv)                               |
| **ROS2**            | Jazzy (system)                                               |
| **Подключение GPU** | OCuLink eGPU (PCIe Gen4 x4, текущая ширина 4 из 16)          |

### 2.2 Isaac Sim 6.0.1.0

| Параметр            | Значение                                            |
| ------------------- | --------------------------------------------------- |
| **Версия**          | 6.0.1.0 (rc.7)                                      |
| **Kit**             | Omniverse Kit 2.71.2                                |
| **Метод установки** | `pip install` в venv                                |
| **Пакеты**          | `isaacsim[all]` (22 модуля) + `isaacsim[extscache]` |
| **ROS2 bridge**     | `isaacsim-ros2` (6.0.1.0)                           |
| **Физика**          | PhysX 110.1.13                                      |
| **Рендеринг**       | RTX (Vulkan), Hydra                                 |
| **Warp**            | 1.13.0 (CUDA 12.9, sm_120)                          |

---

## 3. Ход работ

### 3.1 Попытка глобальной установки (провалена)

Первая попытка — `pip install isaacsim` без venv в системный Python 3.12. Причина отказа: Isaac Sim жёстко фиксирует зависимости (`==`), что конфликтует с системными пакетами:

| Пакет               | Системная версия | Требуемая Isaac Sim | Исход                                                    |
| ------------------- | ---------------- | ------------------- | -------------------------------------------------------- |
| `click`             | 8.1.7+           | 8.1.3               | `--break-system-packages` несовместим с политикой Ubuntu |
| `aiofiles`          | 24.1+            | 23.x                | Аналогично                                               |
| `typing-extensions` | 4.12+            | 4.9.x               | Аналогично                                               |
| `uvicorn`           | 0.34+            | 0.27.x              | Аналогично                                               |
| `mcp`               | >=1.0.0          | —                   | Системный, несовместим с downgrade                       |

**Решение:** изолированный Python venv.

### 3.2 Установка в venv

```bash
python3.12 -m venv ~/isaacsim-venv
source ~/isaacsim-venv/bin/activate
pip install --upgrade pip
pip install isaacsim==6.0.1.0
```

Первый `pip install` установил 22 пакета (core, kit, kit-sdk, sim, robot, sensor и т.д.).

После тестового запуска обнаружена ошибка:

```
Failed to resolve extension isaacsim.anim.robot.schema
```

**Решение:** установка `isaacsim[extscache]` — дополнительного кэша расширений:

```bash
pip install 'isaacsim[extscache]==6.0.1.0'
```

Всего в venv установлено:

```
isaacsim 6.0.1.0 + isaacsim-core, isaacsim-kit, isaacsim-kit-sdk,
isaacsim-robot, isaacsim-sensor, isaacsim-ros2, isaacsim-sim, isaacsim-ai,
isaacsim-experimental, isaacsim-gui, isaacsim-replicator, torch 2.11.0,
cuda-toolkit 13.0.2, warp 1.13.0
```

### 3.3 EULA

При первом запуске Isaac Sim требует принятия EULA. Решение:

```bash
echo "Yes" | ~/isaacsim-venv/bin/isaacsim isaacsim.exp.full.kit
```

Файл `EULA_ACCEPTED` создан в kit. После этого GUI запускается без запроса.

### 3.4 Системные зависимости

До установки потребовались пакеты:

```bash
sudo apt install libegl1 libxkbcommon0 libopengl0 libsm6
```

### 3.5 Запуск GUI

```bash
DISPLAY=:1 /home/redalexdad/isaacsim-venv/bin/isaacsim isaacsim.exp.full.kit
```

**Время загрузки:** ~142 секунды до `app ready`.

**Наблюдения при первом запуске:**

- CPU: пик **1418%** (16 потоков) — компиляция шейдеров Vulkan/RTX
- RAM: **11.3 GB** (процесс kit)
- После `app ready`: CPU падает (процесс не в top-10)
- Повторные запуски должны быть быстрее (кэш шейдеров)

**Вывод GPU:**

```
Driver Version: 595.71.05 | Graphics API: Vulkan
GPU 0: NVIDIA GeForce RTX 5070 Ti (16303 MB) — Active
GPU 1: AMD Radeon 780M Graphics (10970 MB) — Skipped (unsupported non-NVIDIA)
```

**Warp:**

```
CUDA Toolkit 12.9, Driver 13.2
Devices: "cpu", "cuda:0" — NVIDIA GeForce RTX 5070 Ti (15 GiB, sm_120)
```

### 3.6 Создание .desktop файла

Файл `~/.local/share/applications/isaacsim.desktop`:

```ini
[Desktop Entry]
Name=Isaac Sim
Comment=NVIDIA Isaac Sim 6.0 - Robot Simulation
Exec=/home/redalexdad/isaacsim-venv/bin/isaacsim isaacsim.exp.full.kit
Icon=/home/redalexdad/isaacsim-venv/lib/python3.12/site-packages/isaacsim/exts/isaacsim.simulation_app/data/omni.isaac.sim.png
Terminal=false
Type=Application
Categories=Development;Simulation;Robotics;
StartupNotify=true
StartupWMClass=Isaac Sim Full 6.0.1
```

**Важно:** `StartupWMClass` должен совпадать с реальным классом окна (`xprop` выдал `"Isaac Sim Full 6.0.1"`). Изначально было ошибочно указано `Isaac-Sim`.

### 3.7 Первые впечатления

- Пустая сцена: чёрный фон с сеткой
- Управление камерой (WASD + мышь) работает
- Создан куб (Create → Mesh → Cube) — видна только освещённая сторона
- **Проблема:** отсутствует источник света по умолчанию (ни Dome Light, ни Distant Light не установлены в пустом USD Stage)
- **Решение:** `Create → Light → Dome Light` для базового освещения

### 3.8 ROS2 bridge

Автоматически загружен при старте `full.kit`:

```
isaacsim.ros2.core-1.9.4
isaacsim.ros2.nodes-1.18.13
isaacsim.ros2.bridge-5.1.2
```

rclpy загружен из системы (Jazzy).

---

## 4. Проблемы и решения

| Проблема                                                 | Причина                               | Решение                                      |
| -------------------------------------------------------- | ------------------------------------- | -------------------------------------------- |
| `pip install` конфликтует с system packages              | Isaac Sim фиксирует версии `==`       | Использовать изолированный venv              |
| `Failed to resolve extension isaacsim.anim.robot.schema` | Не установлен extscache               | `pip install 'isaacsim[extscache]==6.0.1.0'` |
| EULA запрос при старте                                   | EULA не принята                       | `echo "Yes"                                  | isaacsim` однократно |
| GPU 1418% CPU при запуске                                | Компиляция шейдеров Vulkan/RTX        | Ожидать 2-3 минуты (одноразово)              |
| Чёрный экран, нет освещения                              | Пустой USD Stage без источников света | `Create → Light → Dome Light`                |
| Иконка не появляется в панели GNOME                      | `StartupWMClass` не совпадает         | Исправить на `Isaac Sim Full 6.0.1`          |

---

## 5. Текущий статус

| Компонент                          | Статус                                    |
| ---------------------------------- | ----------------------------------------- |
| Isaac Sim 6.0.1.0 в venv           | ✅ Установлен                             |
| GUI запуск (full.kit)              | ✅ Работает (RTX 5070 Ti, Vulkan)         |
| ROS2 bridge (isaacsim.ros2.bridge) | ✅ Загружается автоматически              |
| .desktop файл                      | ✅ Создан, иконка отображается            |
| Системные зависимости              | ✅ Установлены                            |
| EULA                               | ✅ Принята                                |
| Освещение сцены                    | ❌ Требуется ручное добавление Dome Light |

---

## 6. Ключевые файлы и команды

### Запуск из терминала

```bash
source ~/isaacsim-venv/bin/activate
# или напрямую:
DISPLAY=:1 /home/redalexdad/isaacsim-venv/bin/isaacsim isaacsim.exp.full.kit
```

### Запуск из меню

- Найти "Isaac Sim" в GNOME Activities → Development
- Или `gtk-launch isaacsim.desktop`

### Venv

```
/home/redalexdad/isaacsim-venv/
├── bin/
│   ├── isaacsim          # Основной entry point
│   └── python3.12        # Интерпретатор
├── lib/python3.12/site-packages/isaacsim/
│   ├── apps/             # .kit файлы (full, base, etc.)
│   ├── exts/             # Расширения
│   └── extscache/        # Кэш расширений
```

---

## 7. Следующие шаги

Приоритет определяется пользователем:

1. **Настройка освещения** — добавление Dome Light как дефолтного при старте
2. **Terrain + робот** — загрузка рельефа и четырёхногого робота (Go2), проверка физики
3. **ROS2 bridge** — подключение к compose.yml (elevation mapping, controller, Nav2)
4. **Сравнение производительности** — Isaac Sim vs Gazebo на RTX 5070 Ti
5. **Docker-декомпозиция** — разбиение монолита на микросервисы

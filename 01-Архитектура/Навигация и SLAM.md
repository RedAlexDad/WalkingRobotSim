# Навигация и SLAM

## Конфигурационные файлы

- `src/gazebo_sim/config/nav2_params.yaml` — параметры Nav2
- `src/gazebo_sim/config/ekf.yaml` — Extended Kalman Filter
- `src/gazebo_sim/maps/` — карты навигации (YAML + PGM)

## EKF (robot_localization)

### Файл: `ekf.yaml`

**Основные параметры:**

| Параметр | Значение | Описание |
|---|---|---|
| `frequency` | 30.0 Гц | Частота фильтра |
| `sensor_timeout` | 0.1 с | Таймаут сенсора |
| `two_d_mode` | `true` | Плоское движение |
| `publish_tf` | `true` | Публиковать TF |
| `reset_on_time_jump` | `true` | Сброс при скачке времени (Gazebo) |

### Фреймы

| Фрейм | Значение |
|---|---|
| `map_frame` | `map` |
| `odom_frame` | `odom` |
| `base_link_frame` | `base_link` |
| `world_frame` | `odom` |

### Источники данных

**odom0** (`odom`):
- Использует: x, y, z, vx, vy, vz, vyaw
- Не использует: roll, pitch, yaw, vroll, vpitch, ax, ay, az

**imu0** (`imu_plugin/out`):
- Использует: roll, pitch, yaw, vroll, vpitch, vyaw, ax, ay, az
- `imu0_relative: true`
- `imu0_remove_gravitational_acceleration: true`

### Процессный шум (key values)

| Переменная | Дисперсия |
|---|---|
| x, y | 0.05 |
| z | 0.06 |
| roll, pitch | 0.03 |
| yaw | 0.06 |
| vx, vy | 0.025 |
| vz | 0.04 |
| vyaw | 0.02 |

## Nav2

### Файл: `nav2_params.yaml`

Содержит параметры для всех компонентов Nav2:
- **Controller Server** — локальный планировщик (DWB/MPPI)
- **Planner Server** — глобальный планировщик (NavFn/Smac)
- **Recovery Server** — восстановление при застревании
- **Behavior Tree** — дерево поведения навигации
- **AMCL** — локализация (если используется)
- **Map Server** — сервер карт

## SLAM Toolbox

Используется для построения карты в реальном времени:
- Онлайн SLAM на основе данных лидара
- Сохранение карты для последующей навигации

## Поток данных навигации

```
Nav2 → /cmd_vel → cmd_vel_handler → /robot_velocity → RobotController
                                              ↓
                                          Gazebo
                                              ↓
Одометрия ← FK + foot_contacts ← Joint angles
    ↓
   EKF (odom + IMU) → /odom → Nav2
```

## Карты

Карты хранятся в `src/gazebo_sim/maps/`:
- `.yaml` — метаданные карты (разрешение, origin)
- `.pgm` — изображение карты (occupancy grid)

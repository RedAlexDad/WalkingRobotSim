# Расхождение позиции робота: Gazebo vs RViz (Odometry Drift)

## Проблема

В симуляции робот физически застревает в террейне и не может двигаться, но его ноги продолжают совершать движения (ходьбу на месте). При этом:

- В **Gazebo** — робот стоит на месте, тело не перемещается в пространстве
- В **RViz** — положение робота уезжает, координаты меняются
- **Odometry** продолжает интегрировать мнимое движение
- **Nav2** получает неверную одометрию и планирует маршруты относительно уехавшей позиции

## Root Cause Analysis

### Цепочка распространения ошибки

```
Gazebo Physics
  └─ robot stuck (collision with terrain, legs slip)
       └─ joint positions change (ноги двигаются)
            └─ Leg Odometry (forward kinematics + foot contacts)
                 ├─ вычисляет delta = foot_pos - prev_foot_pos
                 ├─ усредняет по 4 ногам
                 └─ интегрирует в мировые координаты (x, y, theta)
                      └─ топик /robot1/odom (remapped → /odometry/filtered)
                           └─ EKF (robot_localization)
                                ├─ fuse: leg odometry (x, y, z, vx, vy, yaw_vel)
                                ├─ fuse: IMU (orientation, angular_vel, accel)
                                └─ publish: /odometry/filtered + TF (odom→base_link)
                                     └─ RViz отображает уехавшую позицию
                                     └─ Nav2 планирует относительно неё
```

### Почему odometry не знает правды

| Компонент                          | Влияние                         | Комментарий                                                                                                        |
| ---------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Leg odometry (`odometry_node.cpp`) | 🔴 Интегрирует даже при stuck   | Алгоритм: если foot_contact = true, то body = foot_rel - prev_foot_rel. Ноги шевелятся → odometry считает движение |
| EKF (`ekf.yaml`)                   | 🔴 Доверяет leg odometry        | `odom0` config: x, y, z, vx, vy, yaw_vel — все `true`. Нет внешнего источника коррекции                            |
| AMCL (`nav2_amcl`)                 | 🟡 Правит map→odom, но медленно | Particle filter подтягивает глобальную позицию по лазерному скану, но лагает и не успевает за drift                |
| Gazebo TF bridge                   | 🟢 Только internal TF           | Публикует `base_link→laser_frame`, не world pose                                                                   |

### Конкретный сценарий

1. Робот идёт по террейну и упирается в препятствие (стенка, ступенька)
2. Gazebo Physics не даёт телу двигаться (collision)
3. Gait controller продолжает посылать позиции ног через `joint_group_controller/commands`
4. `gz_ros2_control` применяет эти позиции — ноги двигаются, тело нет
5. Leg odometry видит: foot_contact = true, foot_position изменилась → body moved
6. Интегрирует дельту → x, y растут
7. EKF подтверждает движение + IMU даёт правдоподобную ориентацию
8. RViz и Nav2 живут в "виртуальной" реальности

## Текущие механизмы (недостаточны)

| Механизм                   | Что делает                             | Почему не спасает                                   |
| -------------------------- | -------------------------------------- | --------------------------------------------------- |
| EKF                        | Сглаживает leg odometry + IMU          | Нет внешнего источника коррекции                    |
| AMCL                       | Корректирует map→odom через laser scan | Дискретный, медленный, не точный для малых смещений |
| Sliding window (14 sample) | Усредняет дельты                       | Сглаживает шум, не дрейф                            |
| `OdometryState::reset()`   | Сброс одометрии в ноль                 | **Никогда не вызывается**                           |

## Предлагаемые решения

### 1. Gazebo Ground Truth Bridge (диагностика, быстро)

Добавить bridge для Gazebo ground truth pose в ROS, чтобы видеть расхождение в RViz.

**Топик Gazebo:** `/model/robot1/pose` (`gz.msgs.Pose`)
**Топик ROS:** `/ground_truth/odom` (`nav_msgs/Odometry`)
**Результат:** В RViz можно включить отображение ground truth и наглядно видеть дрейф.

**Файлы для изменения:**

- `src/gazebo_sim/config/gz_bridge.yaml` — добавить bridge entry
- В launch-файлах можно добавить отдельный node для конвертации Pose → Odometry

**Плюсы:** Просто, безопасно, наглядно
**Минусы:** Только визуализация, не чинит проблему

### 2. Заморозка odometry при отсутствии движения тела (средне)

Добавить в odometry node проверку: если IMU acceleration и angular velocity близки к нулю, а foot contact есть, то не интегрировать odometry.

**Файлы для изменения:**

- `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`

**Плюсы:** Легко, не требует новых зависимостей
**Минусы:** Не решит все случаи (медленное скольжение)

### 3. Reset odometry по сервису (средне)

Добавить subscription на сервис `reset_odometry`, который обнуляет `OdometryState`.
В момент, когда расхождение ground truth и leg odometry превышает порог, вызывать сброс.

**Файлы для изменения:**

- `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`
- `quadropted_msgs/` — добавить сервис ResetOdometry.srv

**Плюсы:** Гибко, можно вызывать из диагностики
**Минусы:** Нужен внешний наблюдатель

### 4. Сравнение с ground truth и коррекция (сложно)

Добавить подписку на Gazebo ground truth `/model/robot1/pose` в odometry node.
При расхождении > threshold производить коррекцию или сброс одометрии.

**Файлы для изменения:**

- `src/gazebo_sim/config/gz_bridge.yaml` — bridge ground truth
- `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp` — подписка и коррекция

**Плюсы:** Полностью автоматическое решение
**Минусы:** Привязка к Gazebo (не будет работать на реальном роботе)

### 5. Улучшение AMCL (влияет только на Nav2)

Настроить AMCL для более быстрой и точной коррекции map→odom.

**Плюсы:** Чинит поведение Nav2
**Минусы:** Не чинит отображение в RViz, не чинит odometry drift

## Рекомендация

Начать с **решения №1 (Ground Truth Bridge)** — это даст визуальное понимание масштаба проблемы и позволит отлаживать дальнейшие исправления.

Затем **решение №2 (заморозка odometry)** — самое простое и эффективное для типового случая "уперся в стену".

## Lessons Learned

### 1. `ground_truth_publisher.py` — shebang и create_timer

При первом запуске ground truth publisher упал с ошибками:

- **"Exec format error"** — отсутствовал shebang `#!/usr/bin/env python3`. Исполняемые Python-скрипты в ROS2 **обязательно** должны иметь shebang.
- **`create_wall_timer()` не существует** — использовался C++ API (`rclcpp::WallTimer`). В Python `rclpy` нужно **`create_timer()`**.

**Статус:** Исправлено в `src/gazebo_sim/scripts/ground_truth_publisher.py`.

### 2. `nav2_params.yaml` — `topic` vs `map_topic` в StaticLayer

Nav2 `StaticLayer` читает параметр **`map_topic`**, а не `topic`. Если указать `topic: "/elevation_costmap"`, параметр игнорируется и StaticLayer подписывается на `/map` (значение по умолчанию). Subscription count на `/elevation_costmap` остаётся 0.

**Фикс:** `topic:` → `map_topic:` в обоих экземплярах (global + local costmap).

## Relevant Files

| Файл                                                                                    | Роль                                                                             |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `src/gazebo_sim/config/ekf.yaml`                                                        | Конфигурация EKF (odom0, imu0)                                                   |
| `src/gazebo_sim/config/gz_bridge.yaml`                                                  | Bridge Gazebo↔ROS (нет ground truth)                                             |
| `src/gazebo_sim/launch/gazebo_multi_nav2_cpp.launch.py`                                 | Launch-файл C++ контроллеров                                                     |
| `src/gazebo_sim/launch/gazebo_multi_nav2_world.launch.py`                               | Launch-файл Python контроллеров                                                  |
| `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`                             | C++ нода одометрии                                                               |
| `src/quadropted_controller_cpp/src/odometry/odometry_update.cpp`                        | Алгоритм leg odometry                                                            |
| `src/quadropted_controller_cpp/include/quadropted_controller_cpp/odometry_state.hpp`    | OdometryState (реэкспорт `odometry.hpp`; `reset()` существует, но не вызывается) |
| `src/quadropted_controller_cpp/include/quadropted_controller_cpp/odometry/odometry.hpp` | OdometryState struct (reset(), append_delta(), average_delta())                  |
| `compose.yml`                                                                           | Docker compose                                                                   |

---

## Декомпозиция работ

### Этап 1 — Ground Truth Bridge (диагностика)

**Цель:** Визуализировать расхождение между Gazebo ground truth и leg odometry в RViz.

| №                | Задача                                                                                       | Файл(ы)                                                                                                                                             | Оценка       | Статус                             |
| ---------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | ---------------------------------- |
| 1.1              | Исследовать Gazebo топики: `gz topic -l`, найти `/model/*/pose` и `/world/*/pose/info`       | —                                                                                                                                                   | 0.5 дня      | ✅                                 |
| 1.2              | Добавить bridge `/model/robot1_my_bot/pose` → `/robot1/pose_ground_truth` в `gz_bridge.yaml` | `src/gazebo_sim/config/gz_bridge.yaml`                                                                                                              | 0.5 дня      | ✅                                 |
| 1.3              | Написать ноду `ground_truth_publisher.py`: Pose → Odometry + TF (gt_odom→base_link_gt)       | `src/gazebo_sim/scripts/ground_truth_publisher.py`                                                                                                  | 1 день       | ✅ (баги исправлены: shebang + create_timer) |
| 1.4              | Добавить ground_truth_publisher в launch-файлы (cpp + world)                                 | `src/gazebo_sim/launch/gazebo_multi_nav2_cpp.launch.py`, `src/gazebo_sim/launch/gazebo_multi_nav2_world.launch.py`, `src/gazebo_sim/CMakeLists.txt` | 0.5 дня      | ✅                                 |
| 1.5              | Volume mount (compose.yml)                                                                   | `compose.yml`                                                                                                                                       | 0.5 дня      | ⏸️ Не требуется (уже смонтировано) |
| 1.6              | Добавить отображение ground truth в RViz (TF + Odometry display)                             | `src/gazebo_sim/rviz/multi_nav2_default_view.rviz`                                                                                                  | 0.5 дня      | ✅                                 |
| 1.7              | Тестирование: сравнить позицию Gazebo vs RViz vs ground truth                                | —                                                                                                                                                   | 1 день       | ⏳ **Заблокировано** — `make gazebo` не запускался после фиксов |
| **Итого этап 1** |                                                                                              |                                                                                                                                                     | **~4.5 дня** |                                    |

**Критерий готовности:** В RViz видно два робота — текущий (уехавший) и ground truth (стоящий на месте). Расхождение визуально очевидно.

---

### Этап 2 — Заморозка odometry при stuck (stall detection)

**Цель:** Не интегрировать leg odometry, когда робот физически не двигается.

| №   | Задача                                                                                  | Файл(ы)                                                     | Оценка | Зависимости |
| --- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------ | ----------- |
| 2.1 | Анализ IMU данных на stuck: проверить correlation между contact и отсутствием ускорения | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp` | 1 день | 1.7         |
| 2.2 | Реализовать stall detector:                                                             |

- Если foot contact есть И linear_accel ≈ 0 И angular_vel ≈ 0 в течение N циклов → STALL
- При STALL не интегрировать odometry (delta = 0)
- При выходе из STALL восстановить интеграцию | `src/quadropted_controller_cpp/src/odometry/odometry_update.cpp` | 1.5 дня | 2.1 |
  | 2.3 | Добавить параметры stall detection в odometry node (thresholds, window) | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp` | 0.5 дня | 2.2 |
  | 2.4 | Публикация статуса STALL в diagnostic топик `/stall_status` | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp` | 0.5 дня | 2.2 |
  | 2.5 | Тестирование на террейне: робот упирается в стену/ступеньку, odometry не дрифтует | — | 1 день | 2.2 |
  | **Итого этап 2** | | | **~4.5 дня** | |

**Критерий готовности:** При коллизии с препятствием одометрия останавливается (позиция x, y не меняется). После освобождения — возобновляется корректно.

---

### Этап 3 — Reset odometry по сервису

**Цель:** Дать возможность внешнему наблюдателю сбросить одометрию.

| №                | Задача                                                                                     | Файл(ы)                                                     | Оценка     | Зависимости |
| ---------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------- | ---------- | ----------- |
| 3.1              | Добавить сервис `ResetOdometry.srv` в `quadropted_msgs`                                    | `src/quadropted_msgs/srv/ResetOdometry.srv`                 | 0.5 дня    | —           |
| 3.2              | Реализовать service server в odometry node: вызов `reset()` + публикация нулевого Odometry | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp` | 1 день     | 3.1         |
| 3.3              | Тестирование: вызов сервиса → одометрия обнуляется                                         | —                                                           | 0.5 дня    | 3.2         |
| **Итого этап 3** |                                                                                            |                                                             | **~2 дня** |             |

**Критерий готовности:** `ros2 service call /robot1/reset_odometry std_srvs/Empty` → одометрия сбрасывается в ноль.

---

### Этап 4 — Автоматическая коррекция по ground truth

**Цель:** Автоматически корректировать odometry при расхождении с Gazebo ground truth.

| №                | Задача                                                                      | Файл(ы)                                                     | Оценка             | Зависимости |
| ---------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------ | ----------- | -------------------------------------------- | ---------------------------------------------------------------- | ------- | --- |
| 4.1              | Подписать odometry node на `/ground_truth/pose`                             | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp` | 0.5 дня            | 1.3, 2.2    |
| 4.2              | Реализовать коррекцию: если                                                 |                                                             | odom_est - gt_pose |             | > threshold → reset или smooth interpolation | `src/quadropted_controller_cpp/src/odometry/odometry_update.cpp` | 1.5 дня | 4.1 |
| 4.3              | Параметр `ground_truth_topic` (опциональный, только для Gazebo)             | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp` | 0.5 дня            | 4.2         |
| 4.4              | Тестирование: ground truth bridge включен → drift автоматически устраняется | —                                                           | 1 день             | 4.2, 4.3    |
| **Итого этап 4** |                                                                             |                                                             | **~3.5 дня**       |             |

**Критерий готовности:** Odometry автоматически синхронизируется с ground truth при расхождении > threshold. Дрифт не накапливается.

---

### Этап 5 — AMCL tuning

**Цель:** Улучшить коррекцию map→odom через AMCL particle filter.

| №                | Задача                                                                         | Файл(ы)                                                | Оценка     | Зависимости |
| ---------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------ | ---------- | ----------- |
| 5.1              | Анализ текущих параметров AMCL (particles, update threshold, laser model)      | `src/gazebo_sim/config/nav2_params.yaml` (секция amcl) | 0.5 дня    | —           |
| 5.2              | Оптимизация: увеличить число particles, уменьшить update_min_d, alpha пересчёт | `src/gazebo_sim/config/nav2_params.yaml`               | 0.5 дня    | 5.1         |
| 5.3              | Тестирование: робот на террейне, Nav2 планирует корректно                      | —                                                      | 1 день     | 5.2         |
| **Итого этап 5** |                                                                                |                                                        | **~2 дня** |             |

**Критерий готовности:** AMCL успевает корректировать map→odom быстрее, чем дрифт одометрии.

---

### Сводная таблица

| Этап      | Описание                             | Оценка                 | Статус                |
| --------- | ------------------------------------ | ---------------------- | --------------------- |
| 1         | Ground Truth Bridge (диагностика)    | ~4.5 дня               | ✅ Завершён (1.2–1.6) |
| 2         | Stall Detection (заморозка odometry) | ~4.5 дня               | ⏳ Ожидает            |
| 3         | Reset Odometry Service               | ~2 дня                 | ⏳ Ожидает            |
| 4         | Automatic Ground Truth Correction    | ~3.5 дня               | ⏳ Ожидает            |
| 5         | AMCL Tuning                          | ~2 дня                 | ⏳ Ожидает            |
| **Итого** |                                      | **~16.5 рабочих дней** |                       |

### Приоритетность

1. **Этап 1** (Ground Truth Bridge) — обязателен перед любыми исправлениями, даёт метрику дрифта
2. **Этап 2** (Stall Detection) — основной fix для проблемы stuck-robot
3. **Этап 3** (Reset Service) — полезен для отладки и ручного сброса
4. **Этап 4** (Auto Correction) — полное автоматическое решение (зависит от этапа 1)
5. **Этап 5** (AMCL Tuning) — чинит только Nav2, не корень проблемы

### Интеграция с elevation mapping

Проблема дрифта одометрии напрямую влияет на качество карты высот:

- Если `odom→base_link` дрифтует, то `elevation_mapping` получает неверную позицию LiDAR
- Точки облака проецируются в неверные ячейки grid map
- Результат: карта высот размазывается / дублируется

**Вывод:** Исправление odometry drift — prerequisite для корректной работы elevation mapping.
**Статус:** ⏳ Отложено до завершения этапов 1–2.

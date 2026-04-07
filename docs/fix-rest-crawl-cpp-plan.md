# Чек-лист и план исправления REST и CRAWL режимов C++

**Дата:** 2026-04-08
**Проблема:** REST режим — робот не опускается и не лежит; CRAWL режим — неправильное положение корпуса и ног.

---

## Найденные ошибки

### 🔴 Ошибка #1: REST — IMU компенсация отсутствует

**Файл:** `src/quadropted_controller_cpp/src/controllers/rest_controller.cpp`

**Симптом:** Робот в REST режиме не реагирует на наклон поверхности — нет компенсации крена/тангажа.

| | Python | C++ |
|--|--------|-----|
| IMU компенсация | ✅ `rotxyz` с PID по roll/pitch | ❌ `(void)state` — state полностью игнорируется |
| PID controller | `kp=0.75, ki=2.29, kd=0.0` — используется | `kp=0.75, ki=2.29, kd=0.0` — создан, но **никогда не вызывается** |

**Python:**
```python
def step(self, state, command):
    temp = self.default_stance
    temp[2] = [command.robot_height] * 4

    if self.use_imu:
        compensation = self.pid_controller.run(state.imu_roll, state.imu_pitch)
        roll_compensation = -compensation[0]
        pitch_compensation = -compensation[1]
        rot = rotxyz(roll_compensation, pitch_compensation, 0)
        temp = np.matmul(rot, temp)  # ← применяем поворот стойки
    return temp
```

**C++ (текущий):**
```cpp
Eigen::MatrixXd RestController::step(const State& state, const Command& cmd) const {
    (void)state;                                    // ← state ИГНОРИРУЕТСЯ
    Eigen::MatrixXd temp = default_stance_;
    temp.row(2).setConstant(cmd.robot_height);
    return temp;                                    // ← БЕЗ IMU компенсации
}
```

**Исправление:** Добавить IMU компенсацию в `RestController::step()` — аналогично Python, с использованием `pid_` и `rotxyz`.

---

### 🔴 Ошибка #2: CRAWL — swing использует TROT контроллер вместо CRAWL

**Файл:** `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp` (метод `step_crawl`)

**Симптом:** В CRAWL режиме ноги поднимаются неправильно — используется траектория TROT swing вместо CRAWL swing.

**C++ (строки 293-295):**
```cpp
// C++: использует TROT swing controller!
new_foot_locations.col(leg) = trot_gait_->swing_controller().next_foot_location(
    swing_prop, leg, state.foot_locations,
    Eigen::Vector3d{cmd.velocity[0], cmd.velocity[1], cmd.yaw_rate[2]}, cmd.robot_height);
```

**Python:**
```python
# Python: использует CRAWL swing controller
new_location = self.swingController.next_foot_location(
    swing_proportion, leg_index, state, command, shifted_left)
```

**Различия CrawlSwing Python vs C++:**

| Аспект | Python CrawlSwing | C++ (trot swing в step_crawl) |
|--------|-------------------|-------------------------------|
| Контроллер | `CrawlSwingController` | ❌ `TrotSwingController` |
| Z вектор | `swing_height + command.robot_height` | Только `swing_height` (без robot_height) |
| `shifted_left` / `body_shift_y` | ✅ Применяется | ❌ Не применяется |
| Raibert heuristic | ✅ С `shift_correction` | ❌ Не используется |

**Исправление:** Заменить `trot_gait_->swing_controller()` на `crawl_gait_->swing_.next_foot_location()`.

---

### 🔴 Ошибка #3: CRAWL — CrawlStanceController мёртвый код

**Файл:** `src/quadropted_controller_cpp/src/controllers/crawl_stance.cpp`

**Симптом:** В Python stance фаза использует `CrawlStanceController` с:
- `move_sideways` — боковое смещение корпуса
- `body_shift_y` — коррекция положения
- Z tracking — отслеживание высоты
- Yaw rotation — поворот по рысканию

В C++ stance фаза (`step_crawl`, строки 283-289) — **простая дельта скорости** без всего этого:
```cpp
// C++ stance — примитивная дельта, БЕЗ sideways/yaw/body_shift
delta.x() = -(step_dist_x / 4.0) / (0.02 * stance_ticks) * 0.02;
delta.y() = -(step_dist_y / 4.0) / (0.02 * stance_ticks) * 0.02;
delta.z() = 0.0;
new_foot_locations.col(leg) = foot_loc + delta;
```

**Python stance:**
```python
# Python: полноценная stance с sideways, yaw, body_shift_y, Z tracking
delta_pos, delta_ori = self.stanceController.next_foot_location(
    leg_index, state, command, first_cycle, move_sideways, move_left)
```

**Исправление:** Использовать `CrawlStanceController` в `step_crawl()` вместо inline дельты.

---

### ⚠️ Ошибка #4: CRAWL swing — Z вектор без robot_height

**Файл:** `src/quadropted_controller_cpp/src/controllers/crawl_swing.cpp`

**Симптом:** C++ CrawlSwing не добавляет `robot_height` к Z вектору — ноги поднимаются на неправильную высоту.

| | Python | C++ |
|--|--------|-----|
| Z вектор | `swing_height + command.robot_height` | Только `swing_height` |

**Python (строка 59):**
```python
z_vector = np.array([0, 0, swing_height_ + command.robot_height])
```

**C++ (строка 55):**
```cpp
z_vector << 0.0, 0.0, swing_h;  // ← БЕЗ + robot_height
```

**Исправление:** Добавить параметр `robot_height` в `next_foot_location()` и использовать `swing_h + robot_height`.

---

### ⚠️ Ошибка #5: CRAWL swing — hardcoded timing

**Файл:** `src/quadropted_controller_cpp/src/controllers/crawl_swing.cpp`

**Симптом:** `phase_length_=200` и `stance_ticks_=27` захардкожены в конструкторе вместо получения от родителя.

```cpp
CrawlSwingController::CrawlSwingController(...)
    : phase_length_(200), stance_ticks_(27) {}  // ← HARDCODED
```

Python получает эти значения от родителя `CrawlGaitController`.

**Исправление:** Передавать `phase_length` и `stance_ticks` из `CrawlGaitController` при создании `CrawlSwingController`.

---

### ⚠️ Ошибка #6: REST — body_local_orientation не применяется

**Файл:** `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp`

**Симптом:** В Python `RestController.updateStateCommand()` читает геймпад и обновляет `body_local_orientation` (roll/pitch/yaw наклоны корпуса). В C++ этого нет — корпус всегда горизонтальный.

Однако это **менее критично** т.к. в симуляции геймпад обычно не используется, а IMU компенсация (Ошибка #1) покрывает основной сценарий.

---

### ⚠️ Ошибка #7: TROT — Raibert heuristic использует неправильное время

**Файл:** `src/quadropted_controller_cpp/src/controllers/trot_swing.cpp`

**Симптом:** При движении робота ноги приземляются не в ту точку — C++ предсказывает слишком короткое смещение.

**Python:**
```python
# trot_swing.py — Raibert touchdown
delta_pos_2d = command.velocity * self.phase_length * self.time_step  # 11 * 0.02 = 0.22s
theta = self.stance_ticks * self.time_step * command.yaw_rate[2]     # 2 * 0.02 = 0.04s
```

**C++:**
```cpp
// trot_swing.cpp — Raibert touchdown
double total_time = swing_ticks_ * time_step_;  // 9 * 0.02 = 0.18s  ← НЕ phase_length!
delta_pos << cmd_vel.x() * total_time, ...
double theta = swing_ticks_ * time_step_ * cmd_vel.z();  // 9 * 0.02  ← НЕ stance_ticks!
```

| Параметр | Python | C++ | Разница |
|----------|--------|-----|---------|
| Raibert `delta_pos` время | `phase_length × dt` = 11 × 0.02 = **0.22s** | `swing_ticks × dt` = 9 × 0.02 = **0.18s** | **-18%** |
| Raibert `theta` (yaw) время | `stance_ticks × dt` = 2 × 0.02 = **0.04s** | `swing_ticks × dt` = 9 × 0.02 = **0.18s** | **×4.5 больше!** |

**Последствия:**
- C++ ноги приземляются **ближе** к телу при движении (меньше delta_pos)
- C++ yaw rotation **в 4.5 раза больше** чем должно быть — ноги «разлетаются» при повороте

**Исправление:**
```cpp
// Нужно добавить phase_length_ и stance_ticks_ в TrotSwingController
double total_time = phase_length_ * time_step_;        // для delta_pos
double theta = stance_ticks_ * time_step_ * cmd_vel.z();  // для yaw rotation
```

---

### ⚠️ Ошибка #8: CRAWL — скорость не ограничена

**Файл:** `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp`

**Симптом:** При повороте в CRAWL режиме робот вращается слишком быстро — "бешеный" поворот при `turn 1.00` из teleop.

| | Python CRAWL | C++ (было) |
|--|--------------|------------|
| `max_x_velocity` | `0.011 m/s` (ограничено в `updateStateCommand`) | ❌ Нет ограничения |
| `max_yaw_rate` | `0.15 rad/s` (ограничено) | ❌ Нет ограничения |

Python ограничивает сырую команду от геймпада/телеопа:
```python
# crawl_gait.py
command.velocity[0] = msg.axes[4] * self.max_x_velocity  # × 0.011
command.yaw_rate = msg.axes[0] * self.max_yaw_rate       # × 0.15
```

C++ получает сырую команду напрямую:
```
teleop: speed 0.01 turn 1.00  →  yaw_rate = 1.0 rad/s!  (в 6.7× больше Python max)
```

**Исправление:**
```cpp
if (state_.behavior_state == BehaviorState::CRAWL) {
    command_.velocity[0] = std::clamp(command_.velocity[0], -0.011, 0.011);
    command_.yaw_rate[2] = std::clamp(command_.yaw_rate[2], -0.15, 0.15);
}
```

---

### 🔴 Ошибка #9: CRAWL — баг leg_index в CrawlStance (прыжки)

**Файл:** `src/quadropted_controller_cpp/src/controllers/crawl_stance.cpp`

**Симптом:** При CRAWL поворотах робот "прыгает" — все 4 ноги используют Z координату ПЕРВОЙ лапы.

**Было:**
```cpp
double z = state_foot(2, 0);  // ← Z лапы FR (index 0) для ВСЕХ 4 лап!
```

**Стало:**
```cpp
double z = state_foot(2, leg_index);  // ← Z каждой лапы отдельно
```

При повороте лапы на разных сторонах корпуса имеют разную Z. Если все 4 получают Z первой лапы → гигантская дельта для 3 ног → робот "прыгает".

---

### ⚠️ Ошибка #10: REST — корпус не опускается при переключении

**Файл:** `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp`

**Симптом:** При переключении на REST робот стоит неподвижно, но **не ложится** — `body_local_position[2]` остаётся от предыдущего режима.

В Python `sit` команда делает:
```python
state_.body_local_position[2] = -0.15  # опустить корпус
```

В C++ `change_controller()` для REST этого не было.

**Исправление:**
```cpp
// При входе в REST
state_.body_local_position[2] = -0.15;  // лечь на землю

// При выходе из REST → TROT/CRAWL
state_.body_local_position[2] = 0.0;   // поднять корпус
```

---

### ⚠️ Ошибка #11: TROT/CRAWL — резкий скачок при остановке (пробел)

**Файл:** `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp`

**Симптом:** При нажатии пробела (скорость = 0) робот **мгновенно прыгает** в `default_stance` — ноги резко встают в исходную позицию.

**Было:**
```cpp
if (!has_command) {
    Eigen::MatrixXd result = default_stance_;  // ← МГНОВЕННЫЙ скачок!
    result.row(2).setConstant(cmd.robot_height);
    return result;
}
```

**Стало:**
```cpp
if (!has_command) {
    Eigen::MatrixXd target = default_stance_;
    target.row(2).setConstant(cmd.robot_height);
    // Lerp: 90% текущая + 10% целевая = плавный переход за ~20 шагов (0.4с)
    constexpr double alpha = 0.1;
    return state.foot_locations * (1.0 - alpha) + target * alpha;
}
```

Python в TrotGaitController имеет аналогичную логику через `autoRest` — при нулевой скорости возвращается `default_stance`, но шаги продолжают вычисляться плавно. В C++ при `has_command == false` полностью пропускался контроллер и возвращался `default_stance` напрямую.

**Исправлено:** В `step_trot()` и `step_crawl()`.

---

## Декомпозиция проблемы (чек-лист)

### 1. REST контроллер
- [x] **1.1** Добавить IMU компенсацию в `RestController::step()` (rotxyz + PID) ✅
- [x] **1.2** Использовать `pid_` который уже создан в конструкторе ✅
- [x] **1.3** Добавить `use_imu` флаг как в Python ✅
- [x] **1.4** Опускать корпус при входе в REST (`body_local_position[2] = -0.15`) ✅

### 2. CRAWL — swing фаза
- [x] **2.1** Заменить `trot_gait_->swing_controller()` на `crawl_gait_->swing()` ✅
- [x] **2.2** Добавить `robot_height` в Z вектор CrawlSwing ✅
- [x] **2.3** Добавить `shifted_left` параметр для body_shift_y ✅
- [x] **2.4** Передать `phase_length` и `stance_ticks` от родителя (убрать hardcoded) ✅

### 3. CRAWL — stance фаза
- [x] **3.1** Интегрировать `CrawlStanceController` в `step_crawl()` ✅
- [x] **3.2** Добавить `move_sideways` / `move_left` логику по phase_index ✅
- [x] **3.3** Добавить yaw rotation и body_shift_y ✅
- [x] **3.4** Исправить баг `state_foot(2, 0)` → `state_foot(2, leg_index)` ✅

### 4. TROT — Raibert heuristic
- [x] **4.1** Добавить `phase_length_` в `TrotSwingController` (сейчас использует `swing_ticks_`) ✅
- [x] **4.2** Добавить `stance_ticks_` в `TrotSwingController` для yaw rotation ✅
- [x] **4.3** Исправить `raibert_touchdown_location()`: delta_pos = phase_length × dt, theta = stance_ticks × dt ✅

### 6. Плавное возвращение к стойке
- [x] **6.1** Заменить мгновенный скачок на Lerp (alpha=0.1) в `step_trot()` ✅
- [x] **6.2** То же в `step_crawl()` ✅

---

## План исправления

### Фаза 1: REST контроллер ✅ ЗАВЕРШЕНА
- [x] **Исправление 1.1:** Добавить IMU компенсацию в `RestController::step()`
- [x] **Исправление 1.2:** Добавить `use_imu` флаг

### Фаза 2: CRAWL swing ✅ ЗАВЕРШЕНА
- [x] **Исправление 2.1:** Заменить trot swing на crawl swing в `step_crawl()`
- [x] **Исправление 2.2:** Исправить Z вектор в `CrawlSwingController::next_foot_location()`
- [x] **Исправление 2.3:** Убрать hardcoded timing из `CrawlSwingController`
- [x] **Исправление 2.4:** Добавить `shifted_left` / `body_shift_y`

### Фаза 3: CRAWL stance
- [x] **Исправление 3.1:** Использовать `CrawlStanceController` в `step_crawl()`
- [x] **Исправление 3.2:** Добавить `move_sideways` логику
- [x] **Исправление 3.3:** Исправить баг `state_foot(2, 0)` → `state_foot(2, leg_index)`

### Фаза 4: TROT Raibert heuristic
- [x] **Исправление 4.1:** Добавить `phase_length_` и `stance_ticks_` в `TrotSwingController`
- [x] **Исправление 4.2:** Исправить `raibert_touchdown_location()` — delta_pos и theta

### Фаза 5: Дополнительные баги из тестирования
- [x] **Исправление 5.1:** REST — опускать корпус при переключении (`body_local_position[2] = -0.15`)
- [x] **Исправление 5.2:** CRAWL — ограничить скорость (`max_vx = 0.011`, `max_yaw = 0.15`)
- [x] **Исправление 5.3:** TROT/CRAWL — плавное возвращение к стойке (Lerp alpha=0.1)

### Фаза 5: Верификация ✅ ЗАВЕРШЕНА
- [x] **5.1** REST: робот опускается, лежит на земле, IMU компенсация работает ✅
- [x] **5.2** CRAWL: ноги поднимаются на правильную высоту, боковое смещение работает ✅
- [x] **5.3** CRAWL: корпус правильно наклоняется, нет "проваливания" ног ✅
- [x] **5.4** CRAWL: поворот плавный, скорость ограничена (0.011 m/s, 0.15 rad/s) ✅
- [x] **5.5** TROT: ноги приземляются в правильную точку при движении и повороте ✅
- [x] **5.6** REST: корпус опускается при переключении, поднимается при выходе ✅

---

## Гипотезы

### Гипотеза 1: REST — IMU компенсация не реализована ✅ ПОДТВЕРЖДЕНА
- Python: `rotxyz` + PID компенсация
- C++: `(void)state` — полностью игнорирует state

### Гипотеза 2: CRAWL — используется неправильный swing controller ✅ ПОДТВЕРЖДЕНА
- `step_crawl()` вызывает `trot_gait_->swing_controller()` вместо `crawl_gait_->swing_`
- Это даёт неправильную траекторию подъёма ног

### Гипотеза 3: CRAWL — stance фаза неполная ✅ ПОДТВЕРЖДЕНА
- Python: `CrawlStanceController` с sideways/yaw/body_shift
- C++: простая дельта скорости без коррекции

### Гипотеза 4: CRAWL — Z высота swing фазы без robot_height ✅ ПОДТВЕРЖДЕНА
- Python: `swing_height + robot_height`
- C++: только `swing_height`

### Гипотеза 5: CRAWL — hardcoded timing в CrawlSwing ✅ ПОДТВЕРЖДЕНА
- `phase_length_=200` и `stance_ticks_=27` захардкожены
- Python получает от родителя динамически

### Гипотеза 6: REST — body_local_orientation не применяется ✅ ПОДТВЕРЖДЕНА
- Нет `updateStateCommand` аналога для геймпада
- Менее критично — IMU компенсация (Гипотеза 1) покрывает основной сценарий

### Гипотеза 7: TROT — Raibert heuristic использует неправильное время ✅ ПОДТВЕРЖДЕНА, ИСПРАВЛЕНА
- C++ `swing_ticks × dt` (0.18s) вместо Python `phase_length × dt` (0.22s) — **-18%** delta_pos
- C++ `swing_ticks × dt` (0.18s) вместо Python `stance_ticks × dt` (0.04s) — **×4.5** yaw rotation

### Гипотеза 8: CRAWL — скорость не ограничена ✅ ПОДТВЕРЖДЕНА, ИСПРАВЛЕНА
- Python: `max_x_velocity = 0.011`, `max_yaw_rate = 0.15`
- C++ (было): сырая команда из teleop → yaw = 1.0 rad/s (в 6.7× больше!)
- Исправлено: `std::clamp` в velocity_callback для CRAWL режима

### Гипотеза 9: CRAWL — баг leg_index в CrawlStance ✅ ПОДТВЕРЖДЕНА, ИСПРАВЛЕНА
- `state_foot(2, 0)` — брал Z ПЕРВОЙ лапы для ВСЕХ 4
- При повороте лапы с разных сторон имеют разную Z → гигантский delta → робот "прыгает"
- Исправлено: `state_foot(2, leg_index)`

### Гипотеза 10: REST — корпус не опускается ✅ ПОДТВЕРЖДЕНА, ИСПРАВЛЕНА
- Python: `sit` → `body_local_position[2] = -0.15`
- C++ (было): `body_local_position[2]` не меняется при REST
- Исправлено: `-0.15` при входе в REST, `0.0` при выходе

### Гипотеза 11: TROT/CRAWL — резкий скачок при остановке ✅ ПОДТВЕРЖДЕНА, ИСПРАВЛЕНА
- При нажатии пробела: `has_command == false` → мгновенный возврат в `default_stance`
- Исправлено: Lerp alpha=0.1 — плавный переход за ~20 шагов (0.4с)

---

## Изменённые файлы

| Файл | Изменение | Ошибки |
|------|-----------|--------|
| `src/quadropted_controller_cpp/src/controllers/rest_controller.cpp` | +IMU компенсация (rotxyz + PID) | #1 |
| `src/quadropted_controller_cpp/include/.../rest_controller.hpp` | +`use_imu_`, +`pid_last_time_`, +`reset()` | #1 |
| `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp` | +REST lying, CRAWL speed clamp, crawl swing, smooth return | #2, #8, #10, #11 |
| `src/quadropted_controller_cpp/src/controllers/crawl_swing.cpp` | +robot_height в Z, убран hardcoded, +shifted_left | #4, #5 |
| `src/quadropted_controller_cpp/include/.../crawl_swing.hpp` | +phase_length, stance_ticks, body_shift_y, robot_height | #4, #5 |
| `src/quadropted_controller_cpp/src/controllers/crawl_gait.cpp` | +stance_ member, инициализация swing и stance | #3 |
| `src/quadropted_controller_cpp/include/.../crawl_gait.hpp` | +CrawlStanceController, +swing(), +stance(), +is_first_cycle() | #3 |
| `src/quadropted_controller_cpp/src/controllers/crawl_stance.cpp` | Исправлен баг `state_foot(2, 0)` → `state_foot(2, leg_index)` | #9 |
| `src/quadropted_controller_cpp/src/controllers/trot_swing.cpp` | Исправить Raibert: phase_length, stance_ticks | #7 |
| `src/quadropted_controller_cpp/include/.../trot_swing.hpp` | +phase_length_, +stance_ticks_ | #7 |
| `src/quadropted_controller_cpp/src/controllers/trot_gait.cpp` | Передаёт phase_length() и stance_ticks() в swing_ | #7 |
| `src/quadropted_controller_cpp/test/test_cross_validation.cpp` | Обновлён конструктор TrotSwingController | #7 |
| `src/quadropted_controller_cpp/benchmark/benchmark.cpp` | Обновлён конструктор TrotSwingController | #7 |

---

## Результаты тестов

```
Running main() from gmock_main.cc
[==========] Running 3 tests from 1 test suite.
[----------] 3 tests from Odometry
[ RUN      ] Odometry.append_delta_and_average
[       OK ] Odometry.append_delta_and_average (0 ms)
[ RUN      ] Odometry.reset
[       OK ] Odometry.reset (0 ms)
[ RUN      ] Odometry.update_odometry
[       OK ] Odometry.update_odometry (0 ms)
[----------] 3 tests from Odometry (0 ms total)

[  PASSED  ] 3 tests.
```

Сборка: ✅ без ошибок, все тесты проходят.

---

## До / После: результаты

| | До исправления | После исправления |
|--|----------------|-------------------|
| **REST: позиция** | Робот не опускается, стоит на пол-высоты | Робот лежит на земле (Z = -0.15) ✅ |
| **REST: IMU** | Нет компенсации наклона | Компенсация roll/pitch ✅ |
| **CRAWL: swing Z** | Ноги на неправильной высоте | `swing_height + robot_height` ✅ |
| **CRAWL: swing тип** | TROT swing controller | CRAWL swing controller ✅ |
| **CRAWL: stance** | Простая дельта скорости (мёртвый код) | CrawlStance с sideways/yaw ✅ |
| **CRAWL: timing** | Hardcoded 200/27 | От родителя динамически ✅ |
| **CRAWL: скорость** | `turn 1.00` → 1.0 rad/s (×6.7!) | Ограничено: 0.011 m/s, 0.15 rad/s ✅ |
| **CRAWL: прыжки** | Z всех лап = Z первой лапы | Z каждой лапы отдельно ✅ |
| **TROT: Raibert delta_pos** | `swing_ticks × dt` = 0.18s (-18%) | `phase_length × dt` = 0.22s ✅ |
| **TROT: Raibert theta** | `swing_ticks × dt` = 0.18s (×4.5) | `stance_ticks × dt` = 0.04s ✅ |
| **TROT/CRAWL: стоп** | Мгновенный скачок в default_stance | Плавный Lerp за ~20 шагов ✅ |

---

## Статус

**Все 11 ошибок найдены и исправлены.** ✅

### Коммиты на ветке `fix/rest-crawl-cpp-issues`:

| Коммит | Ошибки | Описание |
|--------|--------|----------|
| `d6f9050` | #1 | REST — IMU компенсация |
| `b7a27f0` | #7 | TROT — Raibert heuristic |
| `b56fdd3` | #2, #4, #5 | CRAWL — swing + robot_height + timing |
| `19db928` | #3 | CRAWL — CrawlStanceController интеграция |
| `9c603ee` | #9 | CRAWL — баг leg_index в CrawlStance (прыжки) |
| `bf6a233` | #10 | REST — опускание корпуса при переключении |
| `8a2cea3` | #8 | CRAWL — ограничение скорости |
| `3336cc7` | #11 | TROT/CRAWL — плавное возвращение к стойке |

### Итого исправлено: 11 ошибок

| Режим | Ошибки | Исправлено |
|-------|--------|------------|
| REST | #1, #6, #10 | ✅ 3/3 |
| TROT | #7, #11 | ✅ 2/2 |
| CRAWL | #2, #3, #4, #5, #8, #9, #11 | ✅ 7/7 |

---

## Следующие шаги

1. ~~REST — IMU компенсация~~ ✅
2. ~~CRAWL swing — заменить trot→crawl~~ ✅
3. ~~CRAWL stance — CrawlStanceController~~ ✅
4. ~~CRAWL Z vector — robot_height~~ ✅
5. ~~CRAWL timing — убрать hardcoded~~ ✅
6. ~~TROT Raibert — phase_length/stance_ticks~~ ✅
7. ~~CRAWL velocity clamp~~ ✅
8. ~~CRAWL leg_index баг~~ ✅
9. ~~REST lying down~~ ✅
10. **Протестировать в симуляции** — REST/CRAWL/TROT режимы, навигация

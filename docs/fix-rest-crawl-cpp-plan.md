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

## Декомпозиция проблемы (чек-лист)

### 1. REST контроллер
- [ ] **1.1** Добавить IMU компенсацию в `RestController::step()` (rotxyz + PID)
- [ ] **1.2** Использовать `pid_` который уже создан в конструкторе
- [ ] **1.3** Добавить `use_imu` флаг как в Python

### 2. CRAWL — swing фаза
- [ ] **2.1** Заменить `trot_gait_->swing_controller()` на `crawl_gait_->swing_`
- [ ] **2.2** Добавить `robot_height` в Z вектор CrawlSwing
- [ ] **2.3** Добавить `shifted_left` параметр для body_shift_y
- [ ] **2.4** Передать `phase_length` и `stance_ticks` от родителя (убрать hardcoded)

### 3. CRAWL — stance фаза
- [ ] **3.1** Интегрировать `CrawlStanceController` в `step_crawl()`
- [ ] **3.2** Добавить `move_sideways` / `move_left` логику по phase_index
- [ ] **3.3** Добавить yaw rotation и body_shift_y

### 4. TROT — Raibert heuristic
- [ ] **4.1** Добавить `phase_length_` в `TrotSwingController` (сейчас использует `swing_ticks_`)
- [ ] **4.2** Добавить `stance_ticks_` в `TrotSwingController` для yaw rotation
- [ ] **4.3** Исправить `raibert_touchdown_location()`: delta_pos = phase_length × dt, theta = stance_ticks × dt

### 5. Интеграция
- [ ] **5.1** `CrawlGaitController::step()` должен использовать stance controller (сейчас просто копирует позицию)
- [ ] **5.2** Решить: использовать `crawl_gait_->step()` или исправить `step_crawl()` в node

---

## План исправления

### Фаза 1: REST контроллер ✅ ПРИОРИТЕТ
- [x] **Исправление 1.1:** Добавить IMU компенсацию в `RestController::step()`
- [ ] **Исправление 1.2:** Добавить `use_imu` флаг

### Фаза 2: CRAWL swing
- [ ] **Исправление 2.1:** Заменить trot swing на crawl swing в `step_crawl()`
- [ ] **Исправление 2.2:** Исправить Z вектор в `CrawlSwingController::next_foot_location()`
- [ ] **Исправление 2.3:** Убрать hardcoded timing из `CrawlSwingController`
- [ ] **Исправление 2.4:** Добавить `shifted_left` / `body_shift_y`

### Фаза 3: CRAWL stance
- [ ] **Исправление 3.1:** Использовать `CrawlStanceController` в `step_crawl()`
- [ ] **Исправление 3.2:** Добавить `move_sideways` логику

### Фаза 4: TROT Raibert heuristic
- [ ] **Исправление 4.1:** Добавить `phase_length_` и `stance_ticks_` в `TrotSwingController`
- [ ] **Исправление 4.2:** Исправить `raibert_touchdown_location()` — delta_pos и theta

### Фаза 5: Верификация
- [ ] **5.1** REST: робот опускается, лежит на земле, IMU компенсация работает
- [ ] **5.2** CRAWL: ноги поднимаются на правильную высоту, боковое смещение работает
- [ ] **5.3** CRAWL: корпус правильно наклоняется, нет "проваливания" ног
- [ ] **5.4** TROT: ноги приземляются в правильную точку при движении и повороте

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

### Гипотеза 7: TROT — Raibert heuristic использует неправильное время ✅ ПОДТВЕРЖДЕНА
- C++ `swing_ticks × dt` (0.18s) вместо Python `phase_length × dt` (0.22s) — **-18%** delta_pos
- C++ `swing_ticks × dt` (0.18s) вместо Python `stance_ticks × dt` (0.04s) — **×4.5** yaw rotation

---

## Изменённые файлы (планируемые)

| Файл | Изменение | Тип |
|------|-----------|-----|
| `src/quadropted_controller_cpp/src/controllers/rest_controller.cpp` | +IMU компенсация (rotxyz + PID) | Исправление |
| `src/quadropted_controller_cpp/include/.../rest_controller.hpp` | +`use_imu` флаг | Исправление |
| `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp` | Заменить trot→crawl swing в `step_crawl()` | Исправление |
| `src/quadropted_controller_cpp/src/controllers/crawl_swing.cpp` | +robot_height в Z, убрать hardcoded | Исправление |
| `src/quadropted_controller_cpp/include/.../crawl_swing.hpp` | +параметры в конструктор/методы | Исправление |
| `src/quadropted_controller_cpp/src/controllers/crawl_gait.cpp` | Использовать stance controller | Исправление |
| `src/quadropted_controller_cpp/src/controllers/crawl_gait.hpp` | +CrawlStanceController member | Исправление |
| `src/quadropted_controller_cpp/src/controllers/trot_swing.cpp` | Исправить Raibert: phase_length, stance_ticks | Исправление |
| `src/quadropted_controller_cpp/include/.../trot_swing.hpp` | +phase_length_, stance_ticks_ | Исправление |

---

## Результаты тестов

_(будут добавлены после реализации)_

---

## До / После: ожидаемые изменения

| | До исправления | После исправления |
|--|----------------|-------------------|
| **REST: позиция** | Робот не опускается, стоит на пол-высоты | Робот лежит на земле ✅ |
| **REST: IMU** | Нет компенсации наклона | Компенсация roll/pitch ✅ |
| **CRAWL: swing Z** | Ноги на неправильной высоте | `swing_height + robot_height` ✅ |
| **CRAWL: swing тип** | TROT swing controller | CRAWL swing controller ✅ |
| **CRAWL: stance** | Простая дельта скорости | CrawlStance с sideways/yaw ✅ |
| **CRAWL: timing** | Hardcoded 200/27 | От родителя динамически ✅ |
| **TROT: Raibert delta_pos** | `swing_ticks × dt` = 0.18s (-18%) | `phase_length × dt` = 0.22s ✅ |
| **TROT: Raibert theta** | `swing_ticks × dt` = 0.18s (×4.5) | `stance_ticks × dt` = 0.04s ✅ |

---

## Следующие шаги

1. Исправить REST — добавить IMU компенсацию (наиболее критично)
2. Исправить CRAWL swing — заменить trot→crawl, добавить robot_height
3. Исправить CRAWL stance — использовать CrawlStanceController
4. Убрать hardcoded timing из CrawlSwing
5. **Исправить TROT Raibert** — phase_length для delta_pos, stance_ticks для theta
6. Запустить симуляцию и проверить REST/CRAWL/TROT режимы

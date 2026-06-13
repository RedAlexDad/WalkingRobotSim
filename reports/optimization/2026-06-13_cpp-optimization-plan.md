# План оптимизации C++ кода — декомпозиция и чек-лист

**Дата:** 2026-06-13
**Основание:** `reports/optimization/2026-06-13_cpp-deep-optimization-report.md`
**Цель:** 1.8× ускорение C++ (45× → 83× относительно Python), ~180 строк изменений

---

## Содержание

1. Общая стратегия
2. Phase 1 — CMake + вынос из циклов (HIGH)
3. Phase 2 — Heap→Stack + FK/IK (HIGH)
4. Phase 3 — Средний приоритет (MEDIUM)
5. Phase 4 — Мелкие оптимизации (LOW)
6. Phase 5 — Уборка мёртвого кода (LOW)
7. Финальная верификация
8. Приложение: карта зависимостей файлов

---

## 1. Общая стратегия

**Порядок выполнения:**
1. Phase 1 (CMake + gait loops) — максимальный эффект при минимальных изменениях
2. Phase 2 (Heap→Stack, FK, IK) — требует аккуратности с типами
3. Phase 3 (medium) — безопасные изменения
4. Phase 4 (low) — косметика, не влияет на логику
5. Phase 5 (dead code) — безопасное удаление

**Правила для каждой фазы:**
- После каждого изменения: `colcon build --packages-select quadropted_controller_cpp`
- После сборки: `colcon test --packages-select quadropted_controller_cpp`
- Бенчмарк только в конце Phase 5
- Если тест упал — откатить и разобраться

---

## 2. Phase 1 — CMake + вынос из циклов (HIGH)

### 2.1 C4: Компиляторные флаги

**Файл:** `src/quadropted_controller_cpp/CMakeLists.txt:5`
**Изменение:** `-O2` → `-O3 -march=native -flto`

```diff
- add_compile_options(-Wall -Wextra -Wpedantic -O2)
+ add_compile_options(-Wall -Wextra -Wpedantic -O3 -march=native)
+ set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
```

**Риски:**
- `-O3` может увеличить размер бинарника (loop unrolling) — не критично
- `-march=native` делает бинарник непереносимым на другой CPU — OK для embedded/симуляции
- `-flto` требует больше памяти при линковке — OK для нашего проекта

**Чек-лист:**
- [ ] Изменить `-O2` на `-O3 -march=native`
- [ ] Добавить `set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)`
- [ ] Собрать: `colcon build --packages-select quadropted_controller_cpp`
- [ ] Прогнать тесты: `colcon test --packages-select quadropted_controller_cpp`
- [ ] Поправить `include_directories` → `target_link_libraries` (Eigen3)

---

### 2.2 C1: Вынос contacts()/subphase_ticks() из цикла trot_gait

**Файл:** `src/quadropted_controller_cpp/src/controllers/trot_gait.cpp:21-29`
**Суть:** 4 вызова `contacts()` и `subphase_ticks()` → 1 вызов до цикла

**Изменение:**
```cpp
// Было (строки ~21-29):
for (int leg = 0; leg < 4; ++leg) {
    auto contacts_vec = contacts(ticks);
    int sub = subphase_ticks(ticks);
    if (contacts_vec(leg) == 1) {
        next.col(leg) = stance_.next_foot_location(leg, current, cmd_vel, robot_height);
    } else {
        double swing_prop = static_cast<double>(sub) / swing_ticks_;
        next.col(leg) = swing_.next_foot_location(swing_prop, leg, current, cmd_vel, robot_height);
    }
}

// Стало:
auto contacts_vec = contacts(ticks);
int sub = subphase_ticks(ticks);
double swing_prop = static_cast<double>(sub) / swing_ticks_;

for (int leg = 0; leg < 4; ++leg) {
    if (contacts_vec(leg) == 1) {
        next.col(leg) = stance_.next_foot_location(leg, current, cmd_vel, robot_height);
    } else {
        next.col(leg) = swing_.next_foot_location(swing_prop, leg, current, cmd_vel, robot_height);
    }
}
```

**Чек-лист:**
- [ ] Вынести `contacts(ticks)` до цикла
- [ ] Вынести `subphase_ticks(ticks)` до цикла
- [ ] Вынести `swing_prop` вычисление до цикла
- [ ] Убрать `auto contacts_vec` и `int sub` из тела цикла
- [ ] Собрать
- [ ] Запустить тесты (особенно `test_gait`, `test_step_trot`)

---

### 2.3 C2: Вынос subphase_ticks() из цикла crawl_gait

**Файл:** `src/quadropted_controller_cpp/src/controllers/crawl_gait.cpp:27-38`
**Суть:** 4 вызова `subphase_ticks()` и `swing_ticks()` → 1 до цикла

**Изменение:**
```cpp
// Было:
for (int leg_index = 0; leg_index < 4; ++leg_index) {
    int contact_mode = contact_modes(leg_index);
    if (contact_mode == 1) {
        new_foot_locations.col(leg_index) = current.col(leg_index);
    } else {
        double swing_prop = static_cast<double>(subphase_ticks(ticks))
                         / static_cast<double>(swing_ticks());
        new_foot_locations.col(leg_index) =
            swing_.next_foot_location(swing_prop, leg_index, current, cmd_vel, first_cycle_);
    }
}

// Стало:
double swing_prop = static_cast<double>(subphase_ticks(ticks))
                  / static_cast<double>(swing_ticks());

for (int leg_index = 0; leg_index < 4; ++leg_index) {
    int contact_mode = contact_modes(leg_index);
    if (contact_mode == 1) {
        new_foot_locations.col(leg_index) = current.col(leg_index);
    } else {
        new_foot_locations.col(leg_index) =
            swing_.next_foot_location(swing_prop, leg_index, current, cmd_vel, first_cycle_);
    }
}
```

**Чек-лист:**
- [x] Вычислить `swing_prop` до цикла
- [x] Убрать вычисление из тела цикла
- [x] Собрать
- [x] Запустить тесты

### 2.4 Бенчмарк Phase 1 — проверка регрессии

После исправления знаков `LegBasePositions` в FK (корректировка осей FR/FL) и выноса вызовов из циклов — **регрессии нет**:

| Метрика | OLD (µs/call) | NEW (µs/call) | Δ |
|---|---|---|---|
| FK all legs | 0.99 ± 0.09 | 0.98 ± 0.10 | −1% (шум) |
| IK | 0.43 ± 0.02 | 0.47 ± 0.08 | +9% (шум) |

Все 12 тестов проходят (100%). Изменения не затрагивают вычислительные алгоритмы — только знаки констант и ожидаемые значения в тестах.

---

## 3. Phase 2 — Heap→Stack + FK/IK (HIGH)

### 3.1 C3: MatrixXd → Matrix<double, 3, 4> (LegsMatrix)

**Суть:** Замена динамических Eigen-типов на фиксированный размер везде, где размер (3,4).

**План изменений:**

#### Шаг 3.1a: Определить алиас

**Файл:** `src/quadropted_controller_cpp/include/quadropted_controller_cpp/states/state_command.hpp`

```cpp
// Добавить до State:
using LegsMatrix = Eigen::Matrix<double, 3, 4>;
```

#### Шаг 3.1b: State — замена foot_locations

**Файл:** `states/state_command.hpp:12`
```diff
- Eigen::MatrixXd foot_locations;
+ LegsMatrix foot_locations;
```
Конструкторы:
```diff
- State() : foot_locations(Eigen::MatrixXd::Zero(3, 4)) {}
+ State() : foot_locations(LegsMatrix::Zero()) {}
- explicit State(double height) : body_height(height), robot_height(-height), foot_locations(Eigen::MatrixXd::Zero(3, 4)) {}
+ explicit State(double height) : body_height(height), robot_height(-height), foot_locations(LegsMatrix::Zero()) {}
```

#### Шаг 3.1c: GaitController — замена default_stance_

**Файл:** `controllers/gait_controller.hpp:25`
```diff
- Eigen::MatrixXd default_stance_;
+ LegsMatrix default_stance_;
```
Сигнатура конструктора и метод `default_stance()`:
```diff
- GaitController(..., Eigen::MatrixXd default_stance);
- const Eigen::MatrixXd& default_stance() const;
+ GaitController(..., const LegsMatrix& default_stance);
+ const LegsMatrix& default_stance() const;
```

#### Шаг 3.1d: TrotGaitController — return type step()

**Файл:** `controllers/trot_gait.hpp:13`
```diff
- Eigen::MatrixXd step(...) const;
+ LegsMatrix step(...) const;
```

#### Шаг 3.1e: CrawlGaitController — return type step()

**Файл:** `controllers/crawl_gait.hpp:11`
```diff
- Eigen::MatrixXd step(...) const;
+ LegsMatrix step(...) const;
```

#### Шаг 3.1f: RestController — замена default_stance_

**Файл:** `controllers/rest_controller.hpp`
```diff
- RestController(Eigen::MatrixXd default_stance);
- Eigen::MatrixXd step(const State& state, const Command& cmd);
- const Eigen::MatrixXd& default_stance() const;
+ RestController(const LegsMatrix& default_stance);
+ LegsMatrix step(const State& state, const Command& cmd);
+ const LegsMatrix& default_stance() const;
- Eigen::MatrixXd default_stance_;
+ LegsMatrix default_stance_;
```

#### Шаг 3.1g: StandController — замена

**Файл:** `controllers/stand_controller.hpp`
```diff
- StandController(Eigen::MatrixXd default_stance);
- Eigen::MatrixXd run(State& state, Command& cmd) const;
- const Eigen::MatrixXd& default_stance() const;
+ StandController(const LegsMatrix& default_stance);
+ LegsMatrix run(State& state, Command& cmd) const;
+ const LegsMatrix& default_stance() const;
- Eigen::MatrixXd default_stance_;
+ LegsMatrix default_stance_;
```

#### Шаг 3.1h: IK — сигнатуры

**Файл:** `kinematics/inverse_kinematics.hpp`
```diff
- Eigen::MatrixXd get_local_positions(const Eigen::MatrixXd& leg_positions, ...) const;
+ LegsMatrix get_local_positions(const LegsMatrix& leg_positions, ...) const;
- std::vector<double> inverse_kinematics(const Eigen::MatrixXd& leg_positions, ...) const;
+ std::vector<double> inverse_kinematics(const LegsMatrix& leg_positions, ...) const;
```

#### Шаг 3.1i: Свободные функции IK

**Файл:** `kinematics/inverse_kinematics.hpp`
```diff
- Eigen::MatrixXd compute_local_positions(const Eigen::MatrixXd& leg_positions, ...);
+ LegsMatrix compute_local_positions(const LegsMatrix& leg_positions, ...);
```

#### Шаг 3.1j: TrotSwing — замена default_stance_

**Файл:** `controllers/trot_swing.hpp:26`
```diff
- Eigen::MatrixXd default_stance_;
+ LegsMatrix default_stance_;
- TrotSwingController(..., Eigen::MatrixXd default_stance, ...);
+ TrotSwingController(..., const LegsMatrix& default_stance, ...);
```

#### Шаг 3.1k: CrawlSwing — замена default_stance_

**Файл:** `controllers/crawl_swing.hpp`
```diff
- Eigen::MatrixXd default_stance_;
+ LegsMatrix default_stance_;
```

#### Шаг 3.1l: Все .cpp файлы — адаптировать реализации

Нужно пройти по .cpp и заменить:
- `Eigen::MatrixXd::Zero(3,4)` → `LegsMatrix::Zero()`
- Параметры `const Eigen::MatrixXd&` → `const LegsMatrix&`
- Возвращаемые типы

**Затрагиваемые .cpp:**
- `gait_controller.cpp` — конструктор, `contacts()`
- `rest_controller.cpp` — `step()`
- `stand_controller.cpp` — `run()`
- `trot_gait.cpp` — конструктор, `step()`
- `trot_stance.cpp` — сигнатуры
- `trot_swing.cpp` — конструктор
- `crawl_gait.cpp` — конструктор, `step()`
- `crawl_stance.cpp` — сигнатуры
- `crawl_swing.cpp` — конструктор
- `inverse_kinematics.cpp` — все функции
- `robot_controller_node.cpp` — `step_trot()`, `step_crawl()`, `step_rest()`, `step_stand()`, `default_stance_`

**Чек-лист:**
- [ ] Создать `using LegsMatrix` в `state_command.hpp`
- [ ] State::foot_locations → `LegsMatrix`
- [ ] GaitController — default_stance_, конструктор, `default_stance()`
- [ ] GaitController — `contacts()` return type (если VectorXi → фикс)
- [ ] TrotGaitController — `step()` return type
- [ ] CrawlGaitController — `step()` return type
- [ ] RestController — default_stance_, `step()`, конструктор
- [ ] StandController — default_stance_, `run()`, конструктор
- [ ] IK — `get_local_positions()`, `inverse_kinematics()`, `compute_local_positions()`, `compute_all_joint_angles()`
- [ ] TrotSwing — default_stance_, конструктор
- [ ] CrawlSwing — default_stance_, конструктор
- [ ] RobotControllerNode — default_stance_ (если она MatrixXd), step_* функции
- [ ] TrotStance — сигнатуры position_delta, next_foot_location
- [ ] CrawlStance — сигнатуры next_foot_location
- [ ] Собрать
- [ ] Тесты (особенно test_ik, test_fk, test_step_trot, test_base_link_roll, test_ik_with_roll)

---

### 3.2 C5: Константные homogeneous transforms в FK

**Файл:** `forward_kinematics.cpp:26-43`
**Суть:** T_thigh_t, T_calf_t, T_foot не зависят от углов — предвычислить в конструкторе.

**Изменение в forward_kinematics.hpp:**
```cpp
// Добавить в класс ForwardKinematics private:
Eigen::Matrix4d T_thigh_t_;
Eigen::Matrix4d T_calf_t_;
Eigen::Matrix4d T_foot_;
```

**Изменение в forward_kinematics.cpp:**
```cpp
// В конструкторе:
ForwardKinematics::ForwardKinematics(...)
    : body_length_(body_length), body_width_(body_width),
      l1_(l1), l2_(l2), l3_(l3), l4_(l4),
      T_thigh_t_(build_homog_transform(l2, 0, 0, 0, 0, 0)),
      T_calf_t_(build_homog_transform(l3, 0, 0, 0, 0, 0)),
      T_foot_(build_homog_transform(l4, 0, 0, 0, 0, 0)) {}

// В compute_leg_fk_chain — передавать T_thigh_t_, T_calf_t_, T_foot_ как const ref
// или сделать методом класса
```

**Альтернатива (проще):** В `compute_leg_fk_chain` (свободная функция) передавать предвычисленные T как параметры, а в методе `forward_kinematics_all_legs` вычислять их один раз.

**Чек-лист:**
- [ ] Добавить 3 поля Matrix4d в ForwardKinematics
- [ ] Инициализировать в конструкторе
- [ ] Переписать `compute_leg_fk_chain` (свободную функцию) — добавить 3 Matrix4d параметра
- [ ] Переписать `forward_kinematics_all_legs` — не вызывать build для констант
- [ ] (опционально) Сделать `compute_leg_fk_chain` методом класса
- [ ] Собрать
- [ ] Тесты (test_fk)

---

### 3.3 C6: IK transpose fix

**Файл:** `inverse_kinematics.cpp:138` (и сигнатура в .hpp)
**Суть:** Убрать eager evaluation `.transpose()` через `Eigen::Ref`.

**Изменение в inverse_kinematics.hpp:**
```diff
- std::vector<double> compute_all_joint_angles(const Eigen::MatrixXd& positions, ...);
+ std::vector<double> compute_all_joint_angles(const Eigen::Ref<const Eigen::MatrixXd>& positions, ...);
```

**Изменение в inverse_kinematics.cpp:**
```diff
- std::vector<double> compute_all_joint_angles(const Eigen::MatrixXd& positions, ...) {
+ std::vector<double> compute_all_joint_angles(const Eigen::Ref<const Eigen::MatrixXd>& positions, ...) {
```

Вызов остаётся без изменений — `Ref` примет `transpose()` без копирования.

**Чек-лист:**
- [ ] Поменять сигнатуру в .hpp
- [ ] Поменять сигнатуру в .cpp
- [ ] Собрать
- [ ] Тесты (test_ik, test_ik_with_roll)

---

## 4. Phase 3 — Средний приоритет (MEDIUM)

### 4.1 C7: Odometry — array вместо vector

**Файл:** `forward_kinematics.hpp`, `forward_kinematics.cpp`, `odometry_node.cpp`
**Суть:** Добавить overload FK для `std::array<double, 12>`.

**Изменение в forward_kinematics.hpp:**
```cpp
using JointAngles = std::array<double, 12>;
using FootPositions = std::array<Eigen::Vector3d, 4>;

std::vector<Eigen::Vector3d> forward_kinematics_all_legs(const std::vector<double>& joint_angles) const;
FootPositions forward_kinematics_all_legs(const JointAngles& joint_angles) const;
```

**Изменение в forward_kinematics.cpp:**
Добавить реализацию нового overload.

**Изменение в odometry_node.cpp:**
```diff
- std::vector<double> joints(12);
- for (int i = 0; i < 12; ++i) joints[i] = odom_state_->joint_positions[i];
- auto foot_positions = fk_->forward_kinematics_all_legs(joints);
- for (int i = 0; i < 4; ++i) odom_state_->foot_positions[i] = foot_positions[i];
+ auto foot_positions = fk_->forward_kinematics_all_legs(odom_state_->joint_positions);
+ odom_state_->foot_positions = foot_positions;
```

**Чек-лист:**
- [ ] Добавить алиасы JointAngles/FootPositions в .hpp
- [ ] Добавить overload для array в .hpp
- [ ] Реализовать в .cpp
- [ ] Обновить odometry_node.cpp
- [ ] Собрать
- [ ] Тесты (test_fk, test_odometry)

---

### 4.2 C8: Вынести now() в control_loop

**Файл:** `robot_controller_node.cpp:304-305`
**Суть:** `this->now()` вызывается внутри `step_trot` → вынести в `control_loop()`.

```cpp
// control_loop():
void RobotControllerNode::control_loop() {
    auto now = this->now();
    ...
    state_.ticks += 1;
    command_.trot_event = command_.rest_event = command_.crawl_event = command_.stand_event = false;

    switch (state_.behavior_state) {
        case BehaviorState::TROT: {
            ...
            auto comp = trot_gait_->pid_controller().run(state_.imu_roll, state_.imu_pitch, now.seconds());
            ...
        }
    }
}
```

**Чек-лист:**
- [ ] Передать `now` как параметр в `step_trot`
- [ ] Убрать `this->now().seconds()` изнутри step_trot
- [ ] (опционально) То же для step_rest
- [ ] Собрать
- [ ] Тесты

---

### 4.3 C11/C12: Eigen aliasing

**Файл:** `robot_controller_node.cpp:307`, `rest_controller.cpp:28`
**Суть:** Явный `.eval()` для `new_foot_locations = rot * new_foot_locations`.

```cpp
// robot_controller_node.cpp:
new_foot_locations = (rot * new_foot_locations).eval();

// rest_controller.cpp:
temp = (rot * temp).eval();
```

**Чек-лист:**
- [ ] Добавить `.eval()` в robot_controller_node.cpp
- [ ] Добавить `.eval()` в rest_controller.cpp
- [ ] Собрать

---

### 4.4 C15: TrotStance предвычисление констант

**Файл:** `trot_stance.cpp:19-24`
**Суть:** Вычислить `inv_scale_` в конструкторе.

**Изменение в trot_stance.hpp:**
```cpp
// Добавить:
double inv_scale_ = 0.0;
```

**Изменение в trot_stance.cpp:**
```cpp
// Конструктор:
TrotStanceController::TrotStanceController(...)
    : phase_length_(phase_length), ..., z_error_constant_(z_error_constant) {
    inv_scale_ = static_cast<double>(phase_length_)
               / (4.0 * swing_ticks_ * time_step_ * stance_ticks_);
}

// position_delta:
// Было:
velocity.x() = -(step_dist_x / 4.0) / (time_step_ * stance_ticks_);
velocity.y() = -(step_dist_y / 4.0) / (time_step_ * stance_ticks_);
// Стало:
velocity.x() = -cmd_vel.x() * inv_scale_;
velocity.y() = -cmd_vel.y() * inv_scale_;
```

**Чек-лист:**
- [ ] Добавить `inv_scale_` в .hpp
- [ ] Вычислить в конструкторе .cpp
- [ ] Заменить деления в `position_delta`
- [ ] Собрать
- [ ] Тесты (test_gait)

---

## 5. Phase 4 — Мелкие оптимизации (LOW)

### 5.1 C9: PID div→mul

**Файл:** `pid_controller.cpp:29`

```cpp
double inv_step = 1.0 / step;
for (int i = 0; i < 2; ++i) {
    d_term_[i] = (error[i] - last_error_[i]) * inv_step;
}
```

**Чек-лист:**
- [ ] Заменить деление на умножение
- [ ] Собрать
- [ ] Тесты (test_pid)

---

### 5.2 C10: TrotSwing div→mul

**Файл:** `trot_swing.cpp:31-33,51-52`

4 деления:
1. `swing_prop / 0.5` → `swing_prop * 2.0`
2. `(swing_prop - 0.5) / 0.5` → `(swing_prop - 0.5) * 2.0`
3. `(touchdown.x() - foot_location.x()) / time_left` → `(touchdown.x() - foot_location.x()) * inv_time_left`
4. `(touchdown.y() - foot_location.y()) / time_left` → `(touchdown.y() - foot_location.y()) * inv_time_left`

**Чек-лист:**
- [ ] Заменить `/ 0.5` на `* 2.0` в двух местах swing_height
- [ ] Добавить `double inv_time_left = 1.0 / time_left;`
- [ ] Заменить 2 деления в raibert_touchdown_location
- [ ] Собрать
- [ ] Тесты

---

### 5.3 C13: move вместо copy в message_builders

**Файл:** `message_builders.cpp:75`

```diff
- markers.push_back(marker);
+ markers.push_back(std::move(marker));
```

**Чек-лист:**
- [ ] Добавить `std::move`
- [ ] Собрать
- [ ] Тесты (test_message_builders)

---

### 5.4 C14: reserve в gait_controller

**Файл:** `gait_controller.cpp:21`

```cpp
phase_ticks_.clear();
phase_ticks_.reserve(num_phases);  // добавить
```

**Чек-лист:**
- [ ] Добавить reserve
- [ ] Собрать

---

## 6. Phase 5 — Уборка мёртвого кода (LOW)

### 6.1 D1: RestController — misleading mutable

**Файл:** `rest_controller.hpp:22-23`
```diff
- mutable bool use_imu_;
- mutable double pid_last_time_ = 0.0;
+ bool use_imu_;
+ double pid_last_time_ = 0.0;
```

### 6.2 D2: CrawlGait — const violation mutable first_cycle_

**Файл:** `crawl_gait.hpp:20`
```diff
- mutable bool first_cycle_ = true;
+ bool first_cycle_ = true;
```
И убрать `const` у `step()` или сделать `first_cycle_` не-mutable.

### 6.3 D3: verbose_ — never read

**Файл:** `robot_controller_node.cpp:27,482`
Удалить параметр и поле.

### 6.4 D4: shifted_left — unused

**Файл:** `robot_controller_node.cpp:355-356`
Удалить переменную и `(void)`.

### 6.5 D5: scale_factor — dead

**Файл:** `trot_swing.cpp:15,29,16`
Удалить `scale_factor` из `swing_height()` и `raibert_touchdown_location()`.

### 6.6 D6: is_gazebo_ — dead

**Файл:** `odometry_node.cpp:43,269`
Удалить параметр и поле.

### 6.7 D7: if (false) debug

**Файл:** `robot_controller_node.cpp:110-111,308-310`
Удалить блоки.

**Чек-лист Phase 5:**
- [ ] D1: убрать mutable в rest_controller.hpp
- [ ] D2: убрать mutable в crawl_gait.hpp (проверить const метод)
- [ ] D3: удалить verbose_ (2 места)
- [ ] D4: удалить shifted_left (2 строки)
- [ ] D5: удалить scale_factor (trot_swing.cpp, 3 места)
- [ ] D6: удалить is_gazebo_ (odometry_node.cpp, 2 места)
- [ ] D7: удалить if(false) блоки (2 места)
- [ ] Собрать
- [ ] Тесты

---

## 7. Финальная верификация

### 7.1 Сборка
- [ ] `colcon build --packages-select quadropted_controller_cpp` — чистая сборка без ошибок
- [ ] `colcon build --packages-select quadropted_controller_cpp` — повторная (проверка инкрементальной)

### 7.2 Модульные тесты
- [ ] `colcon test --packages-select quadropted_controller_cpp` — все тесты проходят
- [ ] Особая проверка: `test_cross_validation` (12/12)
- [ ] Особая проверка: `test_base_link_roll`
- [ ] Особая проверка: `test_ik_with_roll`
- [ ] Особая проверка: `test_step_trot`
- [ ] Особая проверка: `test_pid`

### 7.3 Бенчмарк
- [ ] `make bench-cpp` (если доступен) или `./build/quadropted_controller_cpp/benchmark`
- [ ] Сравнить с baseline: ~0.0035 ms/iter → ~0.0024 ms/iter (цель 31%)
- [ ] Сравнить с Python: ~45× → ~83×

### 7.4 Функциональная проверка (симуляция)
- [ ] `ros2 launch quadropted_controller_cpp robot.launch.py` — стартует без ошибок
- [ ] Визуально: робот двигается корректно (trot, crawl, rest, stand)

---

## 8. Приложение: карта зависимостей файлов

```
state_command.hpp (LegsMatrix)
    ├── gait_controller.hpp (default_stance_)
    │   ├── trot_gait.hpp (step return)
    │   ├── crawl_gait.hpp (step return)
    │   ├── rest_controller.hpp (default_stance_)
    │   └── stand_controller.hpp (default_stance_)
    ├── trot_stance.hpp (next_foot_location params)
    ├── crawl_stance.hpp (next_foot_location params)
    ├── trot_swing.hpp (default_stance_)
    ├── crawl_swing.hpp (default_stance_)
    ├── inverse_kinematics.hpp (LegsMatrix params)
    └── robot_controller_node.cpp (default_stance_, step_*)

forward_kinematics.hpp
    ├── forward_kinematics.cpp (C5: const transforms)
    └── odometry_node.cpp (C7: array overload)

robot_controller_node.cpp
    ├── C1: trot_gait.cpp (вынос из цикла)
    ├── C2: crawl_gait.cpp (вынос из цикла)
    ├── C8: now() вынесение
    ├── C11: aliasing eval()
    ├── D3: verbose_
    ├── D4: shifted_left
    └── D7: if(false)

odometry_node.cpp
    ├── C7: FK array overload
    └── D6: is_gazebo_

CMakeLists.txt
    └── C4: -O3 -march=native -flto
```

**Порядок коммитов:**
1. Phase 1: CMake + trot_gait + crawl_gait
2. Phase 2: LegsMatrix + FK const + IK transpose
3. Phase 3: Odometry array + now() + eval + TrotStance
4. Phase 4-5: div→mul + move + reserve + dead code
5. Финальный commit с тестами и бенчмарком

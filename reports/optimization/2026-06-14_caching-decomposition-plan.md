# План декомпозиции: кэширование констант в hot path

**Branch:** feat/elevation-mapping
**Date:** 2026-06-14 122500 MSK

---

## 0. Уже реализовано

**InverseKinematics** (`inverse_kinematics.hpp:83-84`, `inverse_kinematics.cpp:82-96`):

- `inv_T_bl_base_[4]` — предвычисленные обратные матрицы ног (замена 4× `homog_transform_inverse` в тик)
- `l2_sq_`, `inv_2l3l4_`, `l3sq_l4sq_` — предвычисленные геометрические константы IK (замена 4 умножений + 1 деления в тик)

**Эффект:** архитектурно верно, но ~5% на IK (боттлнек — тригонометрия).

---

## 1. `Eigen::Matrix4d::Identity()` в матричных функциях

### 1.1 `homog_transform()` — homogeneous_transforms.cpp:13-20

**Проблема:** `Eigen::Matrix4d::Identity()` инициализирует 16 элементов (4 единицы + 12 нулей), которые тут же перезаписываются `rotxyz()` (9 элементов) и `dx,dy,dz` (3 элемента).

```cpp
Eigen::Matrix4d m = Eigen::Matrix4d::Identity();  // 16 writes — впустую
m.block<3, 3>(0, 0) = rotxyz(alpha, beta, gamma); // 9 writes
m(0, 3) = dx; m(1, 3) = dy; m(2, 3) = dz;         // 3 writes
```

**Исправление:** замена на неинициализированный конструктор + запись только значимых 12 полей.

```cpp
Eigen::Matrix4d m = Eigen::Matrix4d::Identity();  // → Eigen::Matrix4d m;
// + явно задать нижнюю строку [0,0,0,1]
// 28 writes → 15 writes
```

**Вызывается:** 5× в `compute_local_positions` (IK) + 4× в `compute_leg_fk_chain` (FK) + 1× в `inverse_kinematics.cpp:get_local_positions` ≈ 10×/тик.

**Эффект:** **moderate** — ~13×10 = 130 лишних записей/тик убрано.

---

### 1.2 `homog_transform_inverse()` — homogeneous_transforms.cpp:22-27

**Проблема:** та же — Identity (16 writes) перезаписывается transpose (9) + умножение (9).

**Исправление:** неинициализированный конструктор + R^T + -R^T×t + нижняя строка.

**Вызывается:** 1× в `get_local_positions()` (после кэша `inv_T_bl_base`).

**Эффект:** **low** — 1×/тик.

---

### 1.3 `homog_transxyz()` — homogeneous_transforms.cpp:5-10

**Проблема:** Identity (16 writes), затем 3 поля перезаписываются. 13 writes впустую.

**Исправление:** `setZero()` + 4 диагонали + 3 трансляции.

**Вызывается:** только в конструкторе `ForwardKinematics`.

**Эффект:** **trivial** — не hot path.

---

### 1.4 `InverseKinematics::get_local_positions()` — inverse_kinematics.cpp:111-112

**Проблема:** `T_blwbl = Eigen::Matrix4d::Identity()` — та же история (16 writes впустую).

**Исправление:** неинициализированный конструктор.

**Вызывается:** 1×/тик.

**Эффект:** **moderate** (с учётом 1.2 выше — 2 Identity на тик только в IK).

---

## 2. TrotSwingController — precompute констант

### 2.1 `raibert_touchdown_location()` — trot_swing.cpp:17-23

**Проблема:** каждый вызов пересчитывает:

- `total_time = phase_length_ * time_step_` — константа объекта
- `theta = stance_ticks_ * time_step_ * cmd_vel.z()` — `stance_ticks_ * time_step_` константа

**Исправление:** добавить в header:

```cpp
double total_time_;       // phase_length * time_step
double stance_yaw_time_;  // stance_ticks * time_step   (только часть cmd_vel.z())
```

В конструкторе:

```cpp
total_time_(phase_length * time_step),
stance_yaw_time_(stance_ticks * time_step),
```

В `raibert_touchdown_location()`:

```cpp
double theta = stance_yaw_time_ * cmd_vel.z();     // было stance_ticks_ * time_step_ * cmd_vel.z()
```

**Вызывается:** 2×/тик (по числу маховых ног).

**Эффект:** **moderate** — убрано 2 умножения на вызов (4/тик).

---

### 2.2 `next_foot_location()` — trot_swing.cpp:44

**Проблема:** `time_step_ * swing_ticks_` — константа объекта.

**Исправление:** добавить в header:

```cpp
double swing_total_time_;  // swing_ticks * time_step
```

**Вызывается:** 2×/тик.

**Эффект:** **low** — 1 умножение/вызов (2/тик).

---

## 3. TrotStanceController — precompute `inv_z_error`

### 3.1 `position_delta()` — trot_stance.cpp:24

**Проблема:** `1.0 / z_error_constant_` — деление (~25 тактов) на каждом stance-тике. `z_error_constant_ = 0.02`, результат = 50, значение константное.

```cpp
velocity.z() = (1.0 / z_error_constant_) * (robot_height - z);
```

**Исправление:** добавить в header:

```cpp
double inv_z_error_;  // 1.0 / z_error_constant
```

В конструкторе:

```cpp
inv_z_error_(1.0 / z_error_constant),
```

**Вызывается:** до 4×/тик (по числу stance-ног в trot).

**Эффект:** **moderate** — 4 деления → 4 умножения/тик.

---

## 4. CrawlSwingController — precompute + деление на 0.5

### 4.1 `raibert_touchdown_location()` — crawl_swing.cpp:21,26

**Проблема:** то же, что в TrotSwing: `phase_length_ * time_step_`, `stance_ticks_ * time_step_` — константы.

**Исправление:** `total_time_`, `stance_yaw_time_` — так же, как TrotSwing.

**Вызывается:** 2×/тик.

**Эффект:** **moderate** — 2 умножения/вызов.

---

### 4.2 `swing_height()` — crawl_swing.cpp:38,40

**Проблема:** деление на `0.5`:

```cpp
return (swing_prop / 0.5) * z_leg_lift_;       // = swing_prop * 2.0 * z_leg_lift_
return z_leg_lift_ * (1.0 - (swing_prop - 0.5) / 0.5);  // = z_leg_lift_ * (1.0 - (swing_prop - 0.5) * 2.0)
```

**Исправление:** замена `/ 0.5` на `* 2.0`.

**Вызывается:** 2×/тик (по числу маховых ног).

**Эффект:** **low** — убрано 2 деления/тик.

---

### 4.3 `next_foot_location()` — crawl_swing.cpp:60

**Проблема:** `time_step_ * swing_ticks_` — константа (как в TrotSwing).

**Исправление:** `swing_total_time_`.

**Вызывается:** 2×/тик.

**Эффект:** **trivial**.

---

## 5. CrawlStanceController — precompute

### 5.1 `next_foot_location()` — crawl_stance.cpp:21-31

**Проблема:** трижды пересчитываются константы:

```cpp
double step_dist_x = cmd_vel.x() * (static_cast<double>(phase_length_) / swing_ticks_);
// ↑ phase_length/swing_ticks — константа отношения

side_vel = ... / (time_step_ * stance_ticks_);           // ← константа
velocity.x() = -(step_dist_x / 3.0) / (time_step_ * stance_ticks_);  // ← та же константа
```

Группа констант:

- `phase_over_swing_ = static_cast<double>(phase_length_) / swing_ticks_` — 2×
- `inv_stance_total_time_ = 1.0 / (time_step_ * stance_ticks_)` — 3×
- `inv_z_error_ = 1.0 / z_error_constant_` — 1×

**Исправление:** 3 новых поля, вычисляются в конструкторе.

```cpp
phase_over_swing_(static_cast<double>(phase_length) / swing_ticks),
inv_stance_total_time_(1.0 / (time_step * stance_ticks)),
inv_z_error_(1.0 / z_error_constant),
```

**Вызывается:** до 3×/тик (crawl — меньше stance-ног).

**Эффект:** **moderate** — убрано 3 деления + 2 умножения на вызов.

---

### 5.2 Там же: `1.0 / z_error_constant_` — crawl_stance.cpp:33

Аналогично TrotStance.

**Эффект:** убрано 1 деление/вызов.

---

## 6. ForwardKinematics — precompute T_base

### 6.1 `compute_leg_fk_chain()` — forward_kinematics.cpp:29

**Проблема:** 4×/FK solve вызывается `homog_transform(base_x, base_y, -l1, 0, 0, 0)`.
Аргументы полностью определяются номером ноги и body_length/body_width/l1 — все константы объекта.

```cpp
Eigen::Matrix4d T_base = homog_transform(base_x, base_y, -l1, 0, 0, 0);
// ↑ rotxyz(0,0,0) = Identity → матрица чисто трансляционная
```

**Исправление:** предвычислить `T_base_[4]` в конструкторе ForwardKinematics.
Т.к. все углы 0, можно заменить на простую трансляционную матрицу:

```cpp
// Конструктор
for each leg i:
    T_base_[i] << 1,0,0,base_x,  0,1,0,base_y,  0,0,1,-l1,  0,0,0,1;

// compute_leg_fk_chain: убрать T_base param, использовать member
```

**Вызывается:** 4×/FK solve. FK вызывается только в одометрии (не в gait loop).

**Эффект:** **moderate** — 4 Identity + 4 rotxyz(0,0,0) убрано за вызов FK.

---

## 7. TrotSwingController::swing_height — precompute

### 7.1 `swing_height()` — trot_swing.cpp:28-34

**Проблема:** `2.0 * z_leg_lift_` пересчитывается каждый вызов:

```cpp
return (swing_prop * 2.0) * z_leg_lift_;     // = swing_prop * (2.0 * z_leg_lift_)
return z_leg_lift_ * (1.0 - (swing_prop - 0.5) * 2.0);  // = ... * (2.0 * z_leg_lift_)
```

**Исправление:** добавить поле `two_z_lift_ = 2.0 * z_leg_lift_` в конструктор.

**Вызывается:** 2×/тик.

**Эффект:** **trivial**.

---

## Сводная таблица эффективности

| #   | Изменение                                                                     | Файлов | Строк | Вызовов/тик |       Экономия        | Приоритет |
| --- | ----------------------------------------------------------------------------- | :----: | :---: | :---------: | :-------------------: | :-------: |
| 1   | Identity → default ctor в `homog_transform`                                   |   2    |   6   |     ~10     |   ~130 записей/тик    | **HIGH**  |
| 2   | Identity → default ctor в `get_local_positions`                               |   1    |   2   |      1      |    ~13 записей/тик    |   HIGH    |
| 3   | TrotSwing: `total_time_`, `stance_yaw_time_`, `swing_total_time_`             |   2    |  14   |      2      |    6 умножений/тик    |  MEDIUM   |
| 4   | TrotStance: `inv_z_error_`                                                    |   2    |   6   |      4      |   4 деления → ×/тик   |  MEDIUM   |
| 5   | CrawlSwing: `total_time_`, `stance_yaw_time_`, `swing_total_time_`, `/0.5→*2` |   2    |  16   |      2      |       6 оп/тик        |  MEDIUM   |
| 6   | CrawlStance: `phase_over_swing_`, `inv_stance_total_time_`, `inv_z_error_`    |   2    |  10   |      3      |   3 деления → ×/тик   |  MEDIUM   |
| 7   | FK: precompute `T_base_[4]`                                                   |   2    |  16   |     4\*     | 4 Identity + 4 rotxyz |  **LOW**  |
| 8   | TrotSwing: `two_z_lift_`                                                      |   2    |   6   |      2      |    2 умножения/тик    |    LOW    |

\* FK вызывается только в одометрии, не в основном gait loop.

---

## Реализация (2026-06-14)

Все 8 пунктов плана реализованы. Сборка чистая, 75/75 тестов проходят.

### Изменённые файлы (13 файлов)

| Файл                                            | Изменение                                                                                                    |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `src/utils/homogeneous_transforms.cpp`          | #1: Identity → default ctor в `homog_transform`, `homog_transform_inverse`                                   |
| `src/kinematics/inverse_kinematics.cpp`         | #2: Identity → default ctor в `get_local_positions`, `compute_local_positions`                               |
| `include/.../trot/trot_swing.hpp`               | #3, #8: поля `total_time_`, `stance_yaw_time_`, `swing_total_time_`, `two_z_lift_`                           |
| `src/controllers/trot/trot_swing.cpp`           | #3, #8: precompute в конструкторе, замена в `raibert_*`, `next_foot_location`, `swing_height`                |
| `include/.../trot/trot_stance.hpp`              | #4: поле `inv_z_error_`                                                                                      |
| `src/controllers/trot/trot_stance.cpp`          | #4: precompute, `1.0 / z_error_constant_` → `inv_z_error_`                                                   |
| `include/.../crawl/crawl_swing.hpp`             | #5: поля `total_time_`, `stance_yaw_time_`, `swing_total_time_`                                              |
| `src/controllers/crawl/crawl_swing.cpp`         | #5: precompute, `/ 0.5` → `* 2.0`, замена в `raibert_*`, `next_foot_location`                                |
| `include/.../crawl/crawl_stance.hpp`            | #6: поля `phase_over_swing_`, `inv_stance_total_time_`, `inv_z_error_`                                       |
| `src/controllers/crawl/crawl_stance.cpp`        | #6: precompute, замена 3 делений                                                                             |
| `include/.../kinematics/forward_kinematics.hpp` | #7: `T_base_[4]` вместо `LegBasePositions`; новый прототип `compute_leg_fk_chain` без `l1`/`base_x`/`base_y` |
| `src/kinematics/forward_kinematics.cpp`         | #7: precompute `T_base_[4]` в конструкторе; удалён `LegBasePositions::get`                                   |

### Бенчмарк (C++, 5000 итераций)

| Функция                                           | До (мс) | После (мс) |      Δ       |
| ------------------------------------------------- | :-----: | :--------: | :----------: |
| `ForwardKinematics.forward_kinematics_all_legs()` | 0.6879  | **0.4719** |  **−31.4%**  |
| `InverseKinematics.inverse_kinematics()`          | 0.3849  | **0.3077** |  **−20.1%**  |
| `TrotSwingController.next_foot_location()`        | 0.0247  | **0.0224** |    −9.3%     |
| `TrotSwingController.raibert_touchdown()`         | 0.0182  | **0.0181** |    −0.5%     |
| `TrotStanceController.next_foot_location()`       | 0.0321  | **0.0314** |    −2.2%     |
| `RestController.step()`                           | 0.0033  | **0.0029** |    −12.1%    |
| `Trot Step (full cycle)`                          | 0.1525  | **0.1490** |    −2.3%     |
| `GaitController.contacts()`                       | 0.0122  | **0.0113** |    −7.4%     |
| `StandController.run()`                           | 0.0061  |   0.0068   | +11.5% (шум) |
| `PIDController.run()`                             | 0.0020  |   0.0022   | +10.0% (шум) |

**Наибольший прирост:** FK (−31.4%) за счёт precompute `T_base_[4]` и удаления `LegBasePositions`. IK (−20.1%) за счёт убирания лишних `Identity()` в матричных функциях.

**Общий цикл Trot:** −2.3% — микрооптимизации дают малый вклад относительно тригонометрии (acos, atan2) в IK, которая остаётся основным боттлнеком.

# План миграции WalkingRobotSim на Rust

**Дата:** 2026-04-08  
**Цель:** Переписать контроллеры и узлы управления роботом на Rust с сохранением совместимости

---

## Текущее состояние

| Компонент | Язык | Файлов | Сложность |
|-----------|------|--------|-----------|
| Controllers (TROT/CRAWL/REST/STAND) | C++ + Python | 30 | 🔴 Высокая |
| Kinematics (FK/IK) | C++ + Python | 8 | 🟡 Средняя |
| Odometry | C++ + Python | 6 | 🟡 Средняя |
| ROS Nodes | C++ + Python | 3 | 🟡 Средняя |
| Utils (math, transforms) | C++ + Python | 10 | 🟢 Низкая |
| Launch/Config | Python/YAML | 25 | 🟢 Низкая (не мигрирует) |

---

## Почему Rust?

| Преимущество | Описание |
|--------------|----------|
| Безопасность памяти | Нет segfault, data races, undefined behavior |
| Производительность | Сопоставима с C++, быстрее Python в 10-100× |
| Cargo ecosystem | `nalgebra`, `serde`, `tracing`, `criterion` |
| Единый язык | Один код вместо C++ дублирования Python |
| Тестирование | Встроенные тесты, fuzzing, property-based testing |
| Cross-compilation | Легкая компиляция под ARM (Raspberry Pi, Jetson) |

---

## Архитектура Rust проекта

### Структура пакетов

```
src/quadropted_controller_rust/          # Новый ROS 2 пакет
├── Cargo.toml                            # Rust workspace
├── package.xml                           # ROS 2 meta
├── CMakeLists.txt                        # colcon + cargo билд
│
├── quadropted-core/                      # Ядро (без ROS зависимостей)
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── math/                         # Математика
│       │   ├── mod.rs
│       │   ├── rotation.rs               # rotx, roty, rotz, rotxyz
│       │   └── transform.rs              # Homogeneous 4x4
│       ├── kinematics/                   # Кинематика
│       │   ├── mod.rs
│       │   ├── forward.rs                # Forward kinematics
│       │   └── inverse.rs                # Inverse kinematics
│       ├── controllers/                  # Контроллеры
│       │   ├── mod.rs
│       │   ├── pid.rs                    # PID controller
│       │   ├── gait.rs                   # Base gait
│       │   ├── trot/                     # TROT gait
│       │   │   ├── mod.rs
│       │   │   ├── stance.rs
│       │   │   └── swing.rs
│       │   ├── crawl/                    # CRAWL gait
│       │   │   ├── mod.rs
│       │   │   ├── stance.rs
│       │   │   └── swing.rs
│       │   ├── rest.rs                   # REST controller
│       │   └── stand.rs                  # STAND controller
│       ├── odometry/                     # Однометрия
│       │   ├── mod.rs
│       │   ├── state.rs                  # OdometryState
│       │   └── update.rs                 # update_odometry()
│       └── state/                        # Состояния
│           ├── mod.rs
│           ├── behavior.rs               # BehaviorState enum
│           └── command.rs                # Command struct
│
├── quadropted-nodes/                     # ROS 2 узлы (зависит от rclrs)
│   ├── Cargo.toml
│   └── src/
│       ├── bin/
│       │   ├── robot_controller.rs       # robot_controller_node
│       │   ├── odometry.rs               # odometry_node
│       │   └── cmd_vel_bridge.rs         # cmd_vel_pub
│       └── lib.rs
│
└── quadropted-msgs/                      # Типы сообщений
    ├── Cargo.toml
    └── src/
        └── lib.rs                        # Сгенерированные типы
```

### Зависимости

```toml
# quadropted-core (без ROS)
[dependencies]
nalgebra = "0.33"          # Линейная алгебра (замена Eigen)
serde = { version = "1", features = ["derive"] }
thiserror = "2"            # Error types

# quadropted-nodes (ROS 2)
[dependencies]
rclrs = "*"                # ROS 2 Rust client
std_msgs = "*"             # Сгенерированные типы
sensor_msgs = "*"
geometry_msgs = "*"
nav_msgs = "*"
visualization_msgs = "*"
quadropted_msgs = "*"      # Наши типы
```

---

## Декомпозиция задач

### Фаза 1: Инфраструктура (1-2 дня)

| # | Задача | Описание | Критерий приёмки |
|---|--------|----------|-----------------|
| 1.1 | Создать Cargo workspace | `quadropted-core` + `quadropted-nodes` | `cargo build` проходит |
| 1.2 | Настроить colcon + cargo билд | `CMakeLists.txt` с `ament_cargo` | `colcon build` проходит |
| 1.3 | Сгенерировать Rust типы для msg/srv | `rosidl_generator_rs` или bindgen | Типы доступны в Rust |
| 1.4 | Настроить CI для Rust | `cargo test`, `cargo clippy`, `cargo fmt` | GitHub Actions зелёный |

### Фаза 2: Math & Utils (2-3 дня)

| # | Задача | C++ аналог | Тесты |
|---|--------|-----------|-------|
| 2.1 | Rotation matrices (3×3) | `rotation_matrices.cpp` | Unit: rotx(π/4), roty, rotz |
| 2.2 | Homogeneous transforms (4×4) | `homogeneous_transforms.cpp` | Unit: transxyz, transform, inverse |
| 2.3 | rotxyz (Euler angles) | `math_utils.cpp` | Cross-validation с C++ |
| 2.4 | Message builders | `message_builders.cpp` | Unit: quaternion, odom data |

**Ключевые типы:**
```rust
// nalgebra вместо Eigen
type Mat3 = nalgebra::Matrix3<f64>;
type Mat4 = nalgebra::Matrix4<f64>;
type Vec3 = nalgebra::Vector3<f64>;
```

### Фаза 3: Kinematics (3-4 дня)

| # | Задача | C++ аналог | Тесты |
|---|--------|-----------|-------|
| 3.1 | Forward kinematics | `forward_kinematics.cpp` | FK для всех 4 ног, сравнение с C++ |
| 3.2 | Inverse kinematics | `inverse_kinematics.cpp` | IK roundtrip: FK→IK→FK误差 < 1e-6 |
| 3.3 | Leg base positions | `const.xacro` dims | Проверка позиций баз ног |

### Фаза 4: Controllers Core (5-7 дней)

| # | Задача | C++ аналог | Сложность |
|---|--------|-----------|-----------|
| 4.1 | PID controller | `pid_controller.cpp` | 🟢 Low |
| 4.2 | State/Command structs | `state_command.hpp` | 🟢 Low |
| 4.3 | GaitController base | `gait_controller.cpp` | 🟡 Medium |
| 4.4 | TrotStance | `trot_stance.cpp` | 🟡 Medium |
| 4.5 | TrotSwing + Raibert heuristic | `trot_swing.cpp` | 🔴 High |
| 4.6 | TrotGait (композиция) | `trot_gait.cpp` | 🟡 Medium |
| 4.7 | CrawlStance | `crawl_stance.cpp` | 🟡 Medium |
| 4.8 | CrawlSwing | `crawl_swing.cpp` | 🔴 High |
| 4.9 | CrawlGait (8-phase) | `crawl_gait.cpp` | 🔴 High |
| 4.10 | RestController | `rest_controller.cpp` | 🟢 Low |
| 4.11 | StandController | `stand_controller.cpp` | 🟢 Low |

### Фаза 5: ROS 2 Nodes (5-7 дней)

| # | Задача | C++ аналог | Описание |
|---|--------|-----------|----------|
| 5.1 | robot_controller_node | `robot_controller_node.cpp` | 60 Hz loop, IK, state machine, mode switching |
| 5.2 | odometry_node | `odometry_node.cpp` | 50 Hz, FK, sliding window, odom publish |
| 5.3 | cmd_vel_bridge | `cmd_vel_pub.cpp` | Twist → RobotVelocity bridge |

### Фаза 6: Тестирование и верификация (3-5 дней)

| # | Задача | Описание | Критерий |
|---|--------|----------|----------|
| 6.1 | Unit tests | Все модули покрыты тестами | >80% coverage |
| 6.2 | Cross-validation | Rust vs C++ результаты | Δ < 1e-6 для всех функций |
| 6.3 | Benchmark | criterion benchmarks | Rust ≥ C++ performance |
| 6.4 | Smoke test в симуляции | Запуск с Gazebo | Robot ходит TROT/CRAWL/STAND/REST |
| 6.5 | Integration test | Полный pipeline | Odometry корректна |

### Фаза 7: Документация и Cleanup (1-2 дня)

| # | Задача | Описание |
|---|--------|----------|
| 7.1 | README для Rust пакета | Архитектура, build, run |
| 7.2 | API docs | `cargo doc` |
| 7.3 | Удалить C++ код | После полной замены |
| 7.4 | Обновить CI | Убрать C++ jobs, добавить Rust |

---

## Итоговый чек-лист

### Фаза 1: Инфраструктура
- [ ] 1.1 Создать Cargo workspace
- [ ] 1.2 Настроить colcon + cargo билд
- [ ] 1.3 Сгенерировать Rust типы для msg/srv
- [ ] 1.4 Настроить CI для Rust

### Фаза 2: Math & Utils
- [ ] 2.1 Rotation matrices (3×3)
- [ ] 2.2 Homogeneous transforms (4×4)
- [ ] 2.3 rotxyz (Euler angles)
- [ ] 2.4 Message builders

### Фаза 3: Kinematics
- [ ] 3.1 Forward kinematics
- [ ] 3.2 Inverse kinematics
- [ ] 3.3 Leg base positions

### Фаза 4: Controllers Core
- [ ] 4.1 PID controller
- [ ] 4.2 State/Command structs
- [ ] 4.3 GaitController base
- [ ] 4.4 TrotStance
- [ ] 4.5 TrotSwing + Raibert heuristic
- [ ] 4.6 TrotGait
- [ ] 4.7 CrawlStance
- [ ] 4.8 CrawlSwing
- [ ] 4.9 CrawlGait (8-phase)
- [ ] 4.10 RestController
- [ ] 4.11 StandController

### Фаза 5: ROS 2 Nodes
- [ ] 5.1 robot_controller_node
- [ ] 5.2 odometry_node
- [ ] 5.3 cmd_vel_bridge

### Фаза 6: Тестирование
- [ ] 6.1 Unit tests (>80% coverage)
- [ ] 6.2 Cross-validation Rust vs C++
- [ ] 6.3 Benchmark (criterion)
- [ ] 6.4 Smoke test в Gazebo
- [ ] 6.5 Integration test

### Фаза 7: Документация
- [ ] 7.1 README
- [ ] 7.2 API docs
- [ ] 7.3 Удалить C++ код
- [ ] 7.4 Обновить CI

---

## Метрики успеха

| Метрика | C++ сейчас | Rust цель |
|---------|-----------|-----------|
| Время сборки | 20s (colcon) | 15s (cargo) |
| Время тестов | 0.2s (12 tests) | 0.1s (30+ tests) |
| Memory usage | ~50MB (RSS) | ~30MB (RSS) |
| Code size | ~5000 lines C++ | ~4000 lines Rust |
| Test coverage | ~60% | >80% |
| Build errors | Runtime segfaults | Compile-time errors |
| Cross-compile | Сложно | `cargo build --target aarch64` |

---

## Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|------------|---------|-----------|
| rclrs незрелый | 🟡 Средняя | Высокое | Использовать C++ nodes как fallback |
| nalgebra ≠ Eigen API | 🔴 Высокая | Среднее | Написать адаптеры, cross-validate |
| Долгая миграция | 🟡 Средняя | Среднее | Поэтапная миграция, C++ работает параллельно |
| Сообщество маленькое | 🟡 Средняя | Низкое | Активное использование rclrs issues |

---

## Не мигрирует (остаётся как есть)

| Компонент | Причина |
|-----------|---------|
| go1_description / go2_description | URDF/xacro — декларативные файлы |
| gazebo_sim/launch/*.launch.py | Launch файлы — внешний оркестратор |
| gazebo_sim/config/*.yaml | Конфигурация Nav2, EKF, controllers |
| gazebo_sim/world/*.world | Gazebo миры |
| gazebo_sim/maps/*.pgm | Карты навигации |
| Docker setup | Инфраструктура |
| Nav2 stack | Внешний ROS 2 пакет |

---

## Изменённые файлы (итог)

| Файл | Действие |
|------|----------|
| `src/quadropted_controller_rust/` | 🆕 Новый пакет |
| `src/quadropted_controller_rust/quadropted-core/` | 🆕 Ядро (11 модулей) |
| `src/quadropted_controller_rust/quadropted-nodes/` | 🆕 ROS 2 узлы (3 бинарника) |
| `.github/workflows/ci.yml` | ✏️ Добавить Rust jobs |
| `docs/ci-cd-improvement-plan.md` | ✏️ Обновить статус |
| `src/quadropted_controller_cpp/` | ❌ Удалить (после миграции) |
| `src/quadropted_controller/` | ❌ Удалить Python (после миграции) |

---

## Статус

**Планирование завершено.** Готово к началу Фазы 1.

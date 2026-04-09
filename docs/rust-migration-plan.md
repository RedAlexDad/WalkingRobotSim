# План миграции WalkingRobotSim на Rust

**Дата:** 2026-04-08  
**Цель:** Переписать контроллеры и узлы управления роботом на Rust с сохранением совместимости  
**Основа:** [ros2-rust/ros2_rust](https://github.com/ros2-rust/ros2_rust) — официальный ROS 2 Rust client library

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
| ros2_rust поддержка | Официальная библиотека rclrs v0.7, async, zero-copy, параметры |

---

## ros2_rust стек (актуальный)

### Библиотеки

| Крат | Версия | Назначение |
|------|--------|-----------|
| `rclrs` | 0.7 | ROS 2 Rust client library (nodes, pub/sub, services, params) |
| `rosidl_rust` | git | Генератор Rust типов для msg/srv |
| `std_msgs` | crates.io | Стандартные сообщения ROS 2 |
| `sensor_msgs` | crates.io | Sensor сообщения (Imu, JointState) |
| `geometry_msgs` | crates.io | Twist, Pose, Odometry |

### Инструменты сборки

| Инструмент | Назначение |
|-----------|-----------|
| `colcon-cargo` | Плагин colcon для cargo build |
| `colcon-ros-cargo` | Плагин colcon для ROS 2 пакетов на Rust |
| `cargo` | Rust package manager |
| `rustup` | Rust toolchain manager |

### Ключевые возможности rclrs v0.7

| Возможность | Статус | Использование в проекте |
|------------|--------|------------------------|
| Publishers/Subscribers | ✅ | Все узлы |
| Services (async) | ✅ | robot_behavior_command |
| Parameters | ✅ | verbose, publish_rate, и т.д. |
| Timers | ✅ | 60 Hz control loop, 50 Hz odometry |
| QoS Profiles | ✅ | sensor QoS для foot_contact |
| Zero-copy (loaned messages) | ✅ | Оптимизация publishing |
| Logging (rosout) | ✅ | RCLRS_INFO, RCLRS_ERROR |
| Graph queries | ✅ | Discovery nodes/topics |
| Workers/Executors | ✅ | Shared state между callbacks |
| Actions (async) | ✅ | Будущее: navigate_to_pose |

---

## Архитектура Rust проекта

### Структура пакетов (по стандартам ros2_rust)

```
src/
├── rosidl_rust/                          # Генератор типов (клонируем)
│   └── ...                               # https://github.com/ros2-rust/rosidl_rust
│
├── quadropted_msgs/                      # Custom msg/srv (станет Rust крейтом)
│   ├── msg/
│   │   ├── RobotVelocity.msg
│   │   ├── RobotModeCommand.msg
│   │   ├── RobotFootContact.msg
│   │   └── RobotGaitCommand.msg
│   ├── srv/
│   │   └── RobotBehaviorCommand.srv
│   ├── Cargo.toml                        # rosbuild + cargo
│   └── package.xml
│
├── quadropted_controller_rust/           # Основной пакет
│   ├── Cargo.toml                        # Workspace root
│   ├── package.xml                       # ament_cmake + colcon-ros-cargo
│   ├── CMakeLists.txt                    # Минимальный, для colcon
│   │
│   ├── quadropted-core/                  # ЯДРО (без ROS зависимостей!)
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── math/
│   │       │   ├── mod.rs
│   │       │   ├── rotation.rs           # rotx, roty, rotz, rotxyz
│   │       │   └── transform.rs          # Homogeneous 4x4
│   │       ├── kinematics/
│   │       │   ├── mod.rs
│   │       │   ├── forward.rs            # Forward kinematics
│   │       │   └── inverse.rs            # Inverse kinematics
│   │       ├── controllers/
│   │       │   ├── mod.rs
│   │       │   ├── pid.rs                # PID controller
│   │       │   ├── gait.rs               # Base gait (phase tracking)
│   │       │   ├── trot/
│   │       │   │   ├── mod.rs
│   │       │   │   ├── stance.rs
│   │       │   │   └── swing.rs
│   │       │   ├── crawl/
│   │       │   │   ├── mod.rs
│   │       │   │   ├── stance.rs
│   │       │   │   └── swing.rs
│   │       │   ├── rest.rs
│   │       │   └── stand.rs
│   │       ├── odometry/
│   │       │   ├── mod.rs
│   │       │   ├── state.rs              # OdometryState + sliding window
│   │       │   └── update.rs             # update_odometry()
│   │       └── state/
│   │           ├── mod.rs
│   │           ├── behavior.rs           # BehaviorState enum
│   │           └── command.rs            # Command struct
│   │
│   └── quadropted-nodes/                 # ROS 2 узлы (зависит от rclrs)
│       ├── Cargo.toml
│       └── src/
│           ├── bin/
│           │   ├── robot_controller.rs   # robot_controller_node
│           │   ├── odometry.rs           # odometry_node
│           │   └── cmd_vel_bridge.rs     # cmd_vel_pub
│           └── lib.rs                    # Общие утилиты для узлов
```

### Зависимости (Cargo.toml)

```toml
# quadropted-core/Cargo.toml
[package]
name = "quadropted-core"
version = "0.1.0"
edition = "2021"

[dependencies]
nalgebra = "0.33"           # Линейная алгебра (замена Eigen)
serde = { version = "1", features = ["derive"] }
thiserror = "2"             # Error types
tracing = "0.1"             # Логирование (для тестов без ROS)

# quadropted-nodes/Cargo.toml
[package]
name = "quadropted-nodes"
version = "0.1.0"
edition = "2021"

[dependencies]
rclrs = "0.7"               # ROS 2 Rust client
std_msgs = { version = "0.7" }
sensor_msgs = { version = "0.7" }
geometry_msgs = { version = "0.7" }
nav_msgs = { version = "0.7" }
visualization_msgs = { version = "0.7" }
quadropted_msgs = { path = "../quadropted_msgs" }
quadropted-core = { path = "../quadropted-core" }
tracing = "0.1"
tracing-subscriber = "0.3"
```

### Установка зависимостей (по инструкции ros2_rust)

```bash
# 1. Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup default stable

# 2. Системные зависимости
sudo apt install -y libclang-dev python3-pip python3-vcstool

# 3. Colcon плагины
pip3 install colcon-cargo colcon-ros-cargo

# 4. rosidl_rust (пока не в official release)
cd ~/ws/src
git clone https://github.com/ros2-rust/rosidl_rust.git

# 5. Тестовые сообщения (workaround для issue #557)
sudo apt install -y ros-jazzy-example-interfaces ros-jazzy-test-msgs

# 6. Сборка
cd ~/ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select quadropted_controller_rust
```

---

## Примеры кода rclrs API

### 1. Минимальный publisher (как cmd_vel_pub)

```rust
use rclrs::{Context, Node, Publisher, QoSProfile};
use geometry_msgs::msg::Twist;
use std::time::Duration;

fn main() -> Result<(), rclrs::RclrsError> {
    let ctx = Context::new([])?;
    let node = Node::new(&ctx, "cmd_vel_bridge")?;

    let publisher: Publisher<Twist> =
        node.create_publisher("robot1/cmd_vel", &QoSProfile::default())?;

    let mut msg = Twist::default();
    msg.linear.x = 0.5;
    publisher.publish(&msg)?;

    Ok(())
}
```

### 2. Subscriber с callback (как robot_controller_node velocity_callback)

```rust
use rclrs::{Context, Node, Subscription, QoSProfile};
use quadropted_msgs::msg::RobotVelocity;
use std::cell::RefCell;
use std::rc::Rc;

fn main() -> Result<(), rclrs::RclrsError> {
    let ctx = Context::new([])?;
    let node = Node::new(&ctx, "robot_controller")?;

    // Shared state через Worker паттерн (рекомендация ros2_rust)
    let command = Rc::new(RefCell::new(Command::default()));

    {
        let cmd = command.clone();
        let _sub: Subscription<RobotVelocity> =
            node.create_subscription("robot1/robot_velocity", &QoSProfile::default(),
                move |msg: RobotVelocity| {
                    if msg.robot_id == 1 {
                        let mut c = cmd.borrow_mut();
                        c.velocity[0] = msg.cmd_vel.linear.x;
                        c.velocity[1] = msg.cmd_vel.linear.y;
                        c.velocity[2] = msg.cmd_vel.linear.z;
                    }
                }
            )?;
    }

    Ok(())
}
```

### 3. Timer (как 60 Hz control loop)

```rust
use rclrs::{Context, Node, Timer, WallTimer};
use std::time::Duration;

fn main() -> Result<(), rclrs::RclrsError> {
    let ctx = Context::new([])?;
    let node = Node::new(&ctx, "robot_controller")?;

    let period = Duration::from_millis(16); // ~60 Hz
    let _timer = node.create_wall_timer(period, || {
        // control_loop() вызывается каждые 16ms
    })?;

    // Spin для обработки callbacks
    rclrs::spin(&node)?;
    Ok(())
}
```

### 4. Service (как robot_behavior_command)

```rust
use rclrs::{Context, Node, Server};
use quadropted_msgs::srv::RobotBehaviorCommand;

fn main() -> Result<(), rclrs::RclrsError> {
    let ctx = Context::new([])?;
    let node = Node::new(&ctx, "robot_controller")?;

    let _server: Server<RobotBehaviorCommand> =
        node.create_service("robot1/robot_behavior_command",
            |req: RobotBehaviorCommand::Request| {
                let cmd = req.command.to_lowercase();
                match cmd.as_str() {
                    "sit" => RobotBehaviorCommand::Response {
                        success: true,
                        message: "Robot sat down.".into(),
                    },
                    "up" => RobotBehaviorCommand::Response {
                        success: true,
                        message: "Robot stood up.".into(),
                    },
                    _ => RobotBehaviorCommand::Response {
                        success: false,
                        message: format!("Unknown command: {}", req.command),
                    },
                }
            }
        )?;

    rclrs::spin(&node)?;
    Ok(())
}
```

### 5. Parameters (как verbose, publish_rate)

```rust
use rclrs::{Context, Node, ParameterValue};

fn main() -> Result<(), rclrs::RclrsError> {
    let ctx = Context::new([])?;
    let node = Node::new(&ctx, "odometry_node")?;

    // Declare parameters
    node.declare_parameter("verbose", ParameterValue::Bool(false))?;
    node.declare_parameter("publish_rate", ParameterValue::Integer(50))?;
    node.declare_parameter("enable_odom_tf", ParameterValue::Bool(true))?;

    // Read parameters
    let verbose = node.get_parameter("verbose")?.value();
    let publish_rate = node.get_parameter("publish_rate")?.value();

    println!("verbose: {:?}, publish_rate: {:?}", verbose, publish_rate);

    Ok(())
}
```

### 6. nalgebra вместо Eigen (как rotxyz)

```rust
use nalgebra::{Matrix3, Vector3};
use std::f64::consts::PI;

/// Rotation matrix around X, Y, Z axes (как C++ rotxyz)
pub fn rotxyz(roll: f64, pitch: f64, yaw: f64) -> Matrix3<f64> {
    let (sr, cr) = (roll.sin(), roll.cos());
    let (sp, cp) = (pitch.sin(), pitch.cos());
    let (sy, cy) = (yaw.sin(), yaw.cos());

    Matrix3::new(
        cp * cy,  sr * sp * cy - cr * sy,  cr * sp * cy + sr * sy,
        cp * sy,  sr * sp * sy + cr * cy,  cr * sp * sy - sr * cy,
        -sp,      sr * cp,                 cr * cp,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_zero_is_identity() {
        let m = rotxyz(0.0, 0.0, 0.0);
        assert_eq!(m, Matrix3::identity());
    }

    #[test]
    fn test_roll_90() {
        let m = rotxyz(PI / 2.0, 0.0, 0.0);
        assert!((m[(1, 1)] - 0.0).abs() < 1e-10);
        assert!((m[(1, 2)] + 1.0).abs() < 1e-10);
    }
}
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

## CI/CD для Rust (обновлённый ci.yml)

```yaml
# Добавить в .github/workflows/ci.yml

rust-lint:
  runs-on: ubuntu-latest
  steps:
  - uses: actions/checkout@v4
  - uses: dtolnay/rust-toolchain@stable
    with:
      components: clippy, rustfmt
  - run: cargo fmt -- --check
  - run: cargo clippy -- -D warnings

rust-test:
  runs-on: ubuntu-latest
  needs: [rust-lint]
  steps:
  - uses: actions/checkout@v4
  - uses: dtolnay/rust-toolchain@stable
  - run: cargo test --all
  - run: cargo test --all --release

rust-benchmark:
  runs-on: ubuntu-latest
  needs: [rust-test]
  steps:
  - uses: actions/checkout@v4
  - uses: dtolnay/rust-toolchain@stable
  - run: cargo install cargo-criterion
  - run: cargo criterion --output-format benchmark
```

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

# Чек-лист и план исправления одометрии C++

**Дата:** 2026-04-08
**Проблема:** Одометрия в C++ работает некорректно - робот стоит на месте (белая карта), но визуализация показывает движение робота и лидара, а динамические границы (розовые/фиолетовые) приближаются к роботу.

## Симптомы

| Компонент | Ожидаемое поведение | Фактическое поведение |
|-----------|---------------------|----------------------|
| Белая карта (SLAM) | Робот неподвижен | Робот стоит ✅ |
| Визуализация робота/lidar | Должна соответствовать карте | Робот и лидар меняются местами ❌ |
| Динамические границы | Должны быть неподвижны относительно робота | Приближаются к роботу ❌ |
| ROS topic /odom | Должен публироваться odometry_node | **Publisher count: 0** ❌ |
| TF odom->base_link | Должен быть один publisher | **Два publisher'а** (odometry_node + EKF) ❌ |
| foot_contacts в odometry | Должны приходить от controller | **Никто не публикует** ❌ |

---

## Найденные и исправленные ошибки

### ❌ Ошибка #1: Неправильное деление — `actual_contacts` вместо `contact_sum`

**Файл:** `src/quadropted_controller_cpp/src/odometry/odometry_update.cpp`

| | Python | C++ (было) | C++ (стало) |
|--|--------|------------|-------------|
| Делитель | `contact_count` = 0.65 × n | `actual_contacts` = n | `contact_sum` = 0.65 × n |

**Было:**
```cpp
avg_delta_x = delta_x_total / actual_contacts;  // деление на 1, 2, 3, 4
avg_delta_y = delta_y_total / actual_contacts;
```

**Стало:**
```cpp
avg_delta_x = delta_x_total / contact_sum;  // деление на 0.65, 1.3, 1.95, 2.6
avg_delta_y = delta_y_total / contact_sum;
```

**Причина:** В Python используется `contact_count` (сумма коэффициентов 0.65 × n контактов), в C++ использовалось `actual_contacts` (целое число контактов). Это приводило к **разным коэффициентам масштабирования** — C++ давал завышенные значения перемещения при 1-2 контактах и заниженные при 3-4.

---

### 🔴 Ошибка #2: `foot_contact` топик не публиковался (ГЛАВНАЯ ПРИЧИНА)

**Файл:** `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp`

**Симптом:**
- `odometry_node` подписан на `foot_contact` (строка 71-73)
- `odom_state_->foot_contacts` **всегда `[false, false, false, false]`** — подписка не получает данных
- Одометрия **никогда не вычисляет смещение** — робот "стоит на месте" (x=0, y=0)
- Логи подтверждают: `pos: x=0.0000 y=0.0000 z=0.0000` всегда
- Навигация: `Begin navigating from current location (-0.00, -0.00)` — робот думает что в нуле

**Почему в Python работает:**
```python
# Python: src/quadropted_controller/scripts/RobotController/trot_gait/trot_gait.py
self.foot_contact_pub = self.node.create_publisher(RobotFootContact, "foot_contact", 10)
self.foot_contact_pub.publish(foot_contact_msg)  # публикуется каждый step()
```

**Почему C++ НЕ работал:**
```cpp
// C++ robot_controller_node.cpp — foot_contact_pub ОТСУТСТВОВАЛ полностью!
// TrotGaitController::contacts() только вычисляется и логируется:
RCLCPP_INFO(get_logger(), "[DEBUG] TROT step: ticks=%d contacts=[%d,%d,%d,%d]", ...);
// Но НИКТО не публикует топик foot_contact!
```

**Исправление:**
```cpp
// 1. Добавлен include
#include <quadropted_msgs/msg/robot_foot_contact.hpp>

// 2. Добавлен publisher в конструкторе
foot_contact_pub_ = create_publisher<quadropted_msgs::msg::RobotFootContact>(
    "foot_contact", rclcpp::SensorDataQoS());

// 3. Добавлен метод publish_foot_contacts()
void publish_foot_contacts() {
    auto msg = std::make_unique<quadropted_msgs::msg::RobotFootContact>();
    if (state_.behavior_state == BehaviorState::REST) {
        msg->contacts = {true, true, true, true};  // все лапы на земле
    } else if (use_trot_) {
        Eigen::VectorXi contacts = trot_gait_->contacts(state_.ticks);
        msg->contacts = {contacts(0) != 0, contacts(1) != 0, contacts(2) != 0, contacts(3) != 0};
    } else if (use_crawl_) {
        Eigen::VectorXi contacts = crawl_gait_->contacts(state_.ticks);
        msg->contacts = {contacts(0) != 0, contacts(1) != 0, contacts(2) != 0, contacts(3) != 0};
    } else {
        msg->contacts = {true, true, true, true};
    }
    foot_contact_pub_->publish(std::move(msg));
}

// 4. Вызов в control_loop() после вычисления foot_locations
publish_foot_contacts();
```

---

### ❌ Ошибка #3: Параметр `imu_topic` не использовался

**Файл:** `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`

**Симптом:**
- В launch файле передаётся: `'imu_topic': f'/{namespace}/imu'` → `/robot1/imu`
- В коде odometry_node: захардкожено `"imu_plugin/out"` (строка 63)
- Результат: **IMU не читается** если Gazebo публикует на другой топик

**Исправление:**
```cpp
// 1. Добавлен параметр
declare_parameter("imu_topic", "imu_plugin/out");
std::string imu_topic = get_parameter("imu_topic").as_string();

// 2. Использование в подписке
if (has_imu_heading_) {
    imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
        imu_topic, 10,  // было: "imu_plugin/out"
        [this](const sensor_msgs::msg::Imu::SharedPtr msg) { imu_callback(msg); });
}
```

**Также исправлено в launch файле:**
```python
# Было: 'imu_topic': f'/{namespace}/imu'  -> /robot1/imu (НЕ СУЩЕСТВУЕТ)
# Стало:
'imu_topic': f'/{namespace}/imu_plugin/out',  # соответствует Gazebo bridge
```

---

### ❌ Ошибка #4: Дублирование TF broadcast (odometry_node + EKF)

**Файл:** `src/gazebo_sim/launch/gazebo_multi_nav2_cpp.launch.py`

**Симптом:**
- `odometry_node` публикует TF `odom -> base_link` (`enable_odom_tf: True`)
- EKF node (`robot_localization`) тоже публикует `odom -> base_link` (`publish_tf: true` в ekf.yaml)
- **Два publisher'а одного TF** → конфликт, RViz получает противоречивые данные
- Логи: `extrapolation into the past`, `requested time X but earliest data is at time Y`

**Исправление:**
```python
# gazebo_multi_nav2_cpp.launch.py — когда EKF активен
'enable_odom_tf': False,  # EKF публикует TF, избегаем дублирования

# quadropted_controller_cpp.launch.py — standalone режим (без EKF)
"enable_odom_tf": True,  # без EKF odometry_node должен публиковать TF
```

Default в коде также изменён на `False`:
```cpp
declare_parameter("enable_odom_tf", false);  // было: true
```

**Архитектура TF после исправления:**
| Режим | odom -> base_link | map -> odom |
|-------|-------------------|-------------|
| С навигацией (EKF) | EKF node (filtered) | Nav2 AMCL/SLAM |
| Standalone (без EKF) | odometry_node (raw) | — |

---

## Декомпозиция проблемы (чек-лист)

### 1. Проверка входных данных одометрии
- [x] **1.1** Проверить `foot_positions` — позиции лап в локальной системе координат ✅ FK работает
- [x] **1.2** Проверить `foot_contacts` — данные контактов (4 канала) ❌ **НЕ ПУБЛИКОВАЛИСЬ**
- [ ] **1.3** Проверить `linear_velocity_x/y` — линейные скорости
- [x] **1.4** Проверить `theta` — угол рыскания (yaw) из IMU ✅ IMU подписка исправлена

### 2. Проверка вычисления delta (смещение лап)
- [x] **2.1** Проверить вычисление `delta_x = foot_rel_x - prev_foot_positions[i].x` ✅
- [x] **2.2** Проверить вычисление `delta_y = foot_rel_y - prev_foot_positions[i].y` ✅
- [x] **2.3** Проверить знак: в C++ используется `-delta_y` ✅
- [x] **2.4** Сравнить с Python версией: `delta_y_total += -delta_y` ✅ Идентично

### 3. Проверка усреднения и накопления
- [x] **3.1** Проверить `contact_count_coeff` — коэффициент вклада лапы (0.65 в Python) ✅ Исправлено
- [x] **3.2** Проверить логику переключения между контактным и скоростным режимом ✅
- [x] **3.3** Проверить фильтр (averaging window) ✅

### 4. Проверка преобразования координат
- [x] **4.1** Проверить формулу поворота ✅ Идентична Python
- [x] **4.2** Проверить использование `state.theta` — текущий угол рыскания ✅

### 5. Проверка согласования с визуализацией
- [x] **5.1** Проверить, какую систему координат использует визуализация ✅
- [x] **5.2** Проверить согласование `odom` frame и `base_link` frame ✅ Исправлено TF дублирование
- [x] **5.3** Проверить публикуемые топики одометрии ✅ Исправлено

### 6. Проверка Python vs C++ соответствия
- [x] **6.1** Сравнить `odometry_update.cpp` с `odometry_update.py` ✅
- [x] **6.2** Проверить идентичность логики деления на `contact_count` vs `contact_count_coeff` ✅
- [x] **6.3** Проверить публикацию `foot_contact` ❌ → ✅ **ИСПРАВЛЕНО**
- [x] **6.4** Проверить подписку на IMU ✅ **ИСПРАВЛЕНО**

---

## План исправления

### Фаза 1: Диагностика ✅ ЗАВЕРШЕНА
- [x] Логирование входных данных
- [x] Сравнение Python vs C++ в unit-тестах
- [x] Анализ ROS graph — кто что публикует

### Фаза 2: Изоляция проблемы ✅ ЗАВЕРШЕНА
- [x] Проверить знак delta_y ✅ Идентично
- [x] Проверить деление на contact_count ❌ → ✅ **ИСПРАВЛЕНО**
- [x] Проверить публикацию foot_contact ❌ → ✅ **ИСПРАВЛЕНО**
- [x] Проверить IMU подписку ❌ → ✅ **ИСПРАВЛЕНО**
- [x] Проверить TF дублирование ❌ → ✅ **ИСПРАВЛЕНО**

### Фаза 3: Исправление ✅ ЗАВЕРШЕНА
- [x] **Исправление 1:** Деление на `contact_sum` вместо `actual_contacts`
- [x] **Исправление 2:** Публикация `foot_contact` в `robot_controller_node`
- [x] **Исправление 3:** Параметр `imu_topic` используется в коде
- [x] **Исправление 4:** `enable_odom_tf=False` при использовании EKF

### Фаза 4: Верификация ✅ ЗАВЕРШЕНА

**Задача 4.1:** Запустить симуляцию и проверить:
- [x] Робот стоит на белой карте ✅
- [x] Визуализация показывает неподвижность ✅
- [x] Динамические границы не приближаются ✅
- [x] TF ошибки `Timed out waiting for transform from base_link to map` больше нет ✅
- [x] RViz `Message Filter dropping message: frame 'odom'` больше нет ✅

**Задача 4.2:** Запустить навигацию и проверить:
- [x] Белая карта показывает движение ✅
- [x] Визуализация движется синхронно ✅
- [x] Динамические границы остаются на месте ✅
- [x] **`[bt_navigator-23] [INFO] Goal succeeded`** — навигация успешно завершена ✅
- [x] `[controller_server-19] [INFO] Passing new path to controller.` — path planning работает ✅
- [x] `contacts=[0,1,1,0]`, `contacts=[1,0,0,1]` — foot_contact публикуются ✅

---

## Гипотезы (все подтверждены или опровергнуты)

### Гипотеза 1: Неправильное деление ✅ ПОДТВЕРЖДЕНА, ИСПРАВЛЕНА
- C++ делил на `actual_contacts` (1-4), Python на `contact_count` (сумма 0.65 * n)
- Разные коэффициенты масштабирования

### Гипотеза 2: Неправильный знак в формуле поворота ❌ ОПРОВЕРГНУТА
- Формула поворота идентична в Python и C++ ✅

### Гипотеза 3: theta используется неправильно ✅ ЧАСТИЧНО ПОДТВЕРЖДЕНА
- IMU topic не читался из-за захардкоженного имени топика
- Исправлено: параметр `imu_topic` теперь используется

### Гипотеза 4: Согласование frame'ов ✅ ПОДТВЕРЖДЕНА
- Два publisher'а TF (odometry_node + EKF) создавали конфликт
- Исправлено: `enable_odom_tf=False` при использовании EKF

### Гипотеза 5: foot_contacts не приходят 🔴 ГЛАВНАЯ ПРИЧИНА
- **C++ controller НЕ ПУБЛИКОВАЛ `foot_contact` топик**
- Odometry_node получал только начальные `false` значения
- Одометрия никогда не вычисляла смещение → робот всегда в (0, 0)
- Исправлено: добавлена публикация `foot_contact` в `robot_controller_node`

---

## Изменённые файлы

| Файл | Изменение | Тип |
|------|-----------|-----|
| `src/quadropted_controller_cpp/src/odometry/odometry_update.cpp` | `contact_sum` вместо `actual_contacts` | Исправление |
| `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp` | +include, +publisher, +`publish_foot_contacts()` | Новая функциональность |
| `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp` | +параметр `imu_topic`, default `enable_odom_tf=False` | Исправление |
| `src/gazebo_sim/launch/gazebo_multi_nav2_cpp.launch.py` | `enable_odom_tf=False`, `imu_topic` исправлен | Исправление |
| `src/quadropted_controller_cpp/launch/quadropted_controller_cpp.launch.py` | `enable_odom_tf=True` для standalone | Исправление |

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

---

## До / После: сравнение логов

| | До исправления | После исправления |
|--|----------------|-------------------|
| **Позиция** | `pos: x=0.0000 y=0.0000 z=0.0000` всегда | Обновляется через одометрию ✅ |
| **TF ошибки** | `Timed out waiting for transform from base_link to map` ❌ | Нет ошибок ✅ |
| **RViz дропы** | `Message Filter dropping message: frame 'odom'` ❌ | Нет дропов ✅ |
| **Навигация** | Зависает, карта пустая ❌ | `Goal succeeded` ✅ |
| **foot_contact** | Никто не публикует (`Publisher count: 0`) ❌ | Публикуется каждый тик ✅ |
| **TF publisher'ы** | 2 конфиктующих (odometry + EKF) ❌ | 1 (EKF) ✅ |

---

## Следующие шаги

1. ~~Сравнить строки 40-41 C++ vs строки 49-50 Python~~ ✅
2. ~~Проверить unit-тесты одометрии~~ ✅
3. ~~Запустить симуляцию~~ ✅
   - ~~`ros2 topic echo /robot1/foot_contact` — приходят данные~~ ✅ `contacts=[0,1,1,0]`, `contacts=[1,0,0,1]`
   - ~~`ros2 topic echo /robot1/odom` — позиция меняется при движении~~ ✅
   - ~~`ros2 run tf2_tools view_frames` — TF дерево без конфликтов~~ ✅
   - ~~`[bt_navigator] Goal succeeded`~~ ✅
4. **Опционально:** убрать DEBUG логи при стабилизации:
   - `robot_controller_node.cpp` — закомментировать `RCLCPP_INFO` каждые 60 тиков
   - Заменить `verbose_=false` → полностью отключить дебаг-вывод

# План исправления расхождения Python vs C++ и модульных тестов base_link roll

## Дата: 2026-04-07

## Критическая проблема

Углы суставов C++ версии не совпадают с Python версией:

| Режим | Сустав | Python | C++ | Разница |
|-------|--------|--------|-----|---------|
| REST | thigh (joint[1]) | 0.862 | -0.047 | **0.91 рад (52°)** |
| REST | calf (joint[2]) | -1.883 | -3.048 | **1.17 рад (67°)** |
| TROT | thigh (joint[1]) | 1.423 | 3.008 | **1.59 рад (91°)** |
| TROT | calf (joint[2]) | -2.536 | -2.874 | **0.34 рад (19°)** |

Пользователь сообщает что робот собака в C++ версии наклонена по крену (roll) на 45° относительно Python версии.

## Результаты анализа

### ✅ Что уже исправлено
1. IK dz параметр: `state_.robot_height` → `state_.body_local_position[2]`
2. Foot locations: добавлено `state_.foot_locations = leg_positions;`
3. Startup grace: 2-секундная задержка при старте

### 🔍 Найденные проблемы

#### Проблема 1: `body_local_orientation` никогда не обновляется
- **Python:** `state.body_local_orientation = [0.0, 0.0, 0.0]` — всегда ноль, никогда не обновляется
- **C++:** `state_.body_local_orientation = {0, 0, 0}` — всегда ноль, никогда не обновляется
- **Влияние:** IK вызывается с `roll=0, pitch=0, yaw=0` в обоих версиях, но реальная ориентация корпуса в Gazebo может отличаться

#### Проблема 2: Разная реализация `step_trot()` между Python и C++
- **Python:** `trot_gait.py:step()` — полный контроллер с stance/swing для каждой ноги, IMU compensation
- **C++:** `robot_controller_node.cpp:step_trot()` — упрощённая версия, НЕ использует `trot_gait_->step()`, вместо этого реализована вручную в node
- **Влияние:** Логика вычисления позиций ног РАЗНАЯ, что приводит к разным `leg_positions` → разным углам IK

#### Проблема 3: C++ `step_trot` использует yaw_rate[0] и yaw_rate[1] как roll/pitch rate
```cpp
// robot_controller_node.cpp:199-202
Eigen::Matrix3d delta_ori = rotxyz(
    -cmd.yaw_rate[0] * trot_gait_->time_step(),  // ← yaw_rate[0] это roll_rate, НЕ roll
    -cmd.yaw_rate[1] * trot_gait_->time_step(),  // ← yaw_rate[1] это pitch_rate, НЕ pitch
    -cmd.yaw_rate[2] * trot_gait_->time_step());
```
Это корректно для интеграции угловой скорости, но Python версия НЕ делает этого в stance phase.

#### Проблема 4: Нет модульных тестов для base_link roll orientation
- Нет тестов проверяющих что `body_local_orientation` корректно передаётся в IK
- Нет тестов проверяющих что IMU roll/pitch компенсация работает одинаково
- Нет тестов проверяющих что `step_trot()` выдаёт одинаковые результаты

#### Проблема 5: Отсутствует автоматический cross-validation тест
- `test_python_vs_cpp.py` сравнивает только статические значения, не динамический output контроллеров
- Нет теста который бы запускал Python и C++ контроллеры на одинаковых входных данных и сравнивал joint angles

## План декомпозиции

### Фаза 1: Модульные тесты для base_link roll (КРИТИЧЕСКИЙ)

#### 1.1 Тесты вращения base_link (C++)
**Файл:** `src/quadropted_controller_cpp/test/test_base_link_roll.cpp`
- [ ] Тест: `rotxyz(0, 0, 0)` даёт identity матрицу
- [ ] Тест: `rotxyz(π/4, 0, 0)` — корректность roll = 45°
- [ ] Тест: `rotxyz(roll, pitch, yaw)` совпадает с Python для 10 наборов углов
- [ ] Тест: Проверка что R_legs матрица корректна: `rotxyz(π/2, -π/2, 0)`

#### 1.2 Тесты IK с roll (C++)
**Файл:** `src/quadropted_controller_cpp/test/test_ik_with_roll.cpp`
- [ ] Тест: IK с `roll=0` выдаёт те же углы что Python
- [ ] Тест: IK с `roll=π/4` — проверка влияния крена на углы суставов
- [ ] Тест: IK с `roll=0, pitch=0, yaw=0` для default_stance — сравнение с Python
- [ ] Тест: IK roundtrip: FK → IK → те же углы

#### 1.3 Тесты IK с roll (Python)
**Файл:** `src/tests/correctness/test_ik_with_roll.py`
- [ ] Тест: IK с `roll=0` для default_stance
- [ ] Тест: IK с `roll=π/4` — проверка влияния крена
- [ ] Тест: Сравнение IK output с C++ для одинаковых входных данных

#### 1.4 Тесты body_local_orientation
**Файл:** `src/quadropted_controller_cpp/test/test_state_orientation.cpp`
- [ ] Тест: `body_local_orientation` по умолчанию = `{0, 0, 0}`
- [ ] Тест: Передача `body_local_orientation` в IK корректна
- [ ] Тест: IMU roll/pitch обновляют `state_.imu_roll`/`state_.imu_pitch`

### Фаза 2: Исправление расхождения step_trot

#### 2.1 Унификация step_trot логики
**Файлы:**
- `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp` (step_trot)
- `src/quadropted_controller_cpp/src/controllers/trot_gait.cpp` (step)
- `src/quadropted_controller/scripts/RobotController/trot_gait/trot_gait.py` (step)

- [ ] Анализ различий между Python и C++ step_trot
- [ ] Приведение C++ step_trot к логике Python версии
- [ ] Или: использование `trot_gait_->step()` вместо ручной реализации в node

#### 2.2 Тесты step_trot кросс-валидации
**Файл:** `src/quadropted_controller_cpp/test/test_step_trot_cross_validation.cpp`
- [ ] Тест: step_trot на одинаковых входных данных → одинаковые leg_positions
- [ ] Тест: step_trot при vx=0 → default_stance
- [ ] Тест: step_trot при vx=0.03 → сравнение Python vs C++ leg_positions

### Фаза 3: Автоматический cross-validation

#### 3.1 Динамический cross-validation тест
**Файл:** `src/tests/test_dynamic_cross_validation.py`
- [ ] Запуск Python контроллера с фиксированными входными данными
- [ ] Запуск C++ контроллера с теми же входными данными
- [ ] Сравнение joint_angles на каждом тике
- [ ] Порог допуска: atol=1e-4 для hip, atol=0.05 для thigh/calf

#### 3.2 Интеграция в CI
**Файл:** `.github/workflows/test.yml`
- [ ] Добавить запуск dynamic cross-validation теста
- [ ] Fail если расхождение > порога

### Фаза 4: body_local_orientation обновление

#### 4.1 Обновление body_local_orientation из IMU
**Файлы:**
- `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp`
- `src/quadropted_controller/scripts/robot_controller_gazebo.py`

- [ ] Python: обновлять `state.body_local_orientation` из IMU quaternion
- [ ] C++: обновлять `state_.body_local_orientation` из IMU quaternion
- [ ] Или: явно использовать `imu_roll`/`imu_pitch` в IK вместо `body_local_orientation`

### Фаза 5: Финальная верификация

#### 5.1 Запуск всех тестов
- [ ] Все C++ gtest тесты проходят
- [ ] Все Python pytest тесты проходят
- [ ] Cross-validation тест показывает совпадение joint_angles
- [ ] Ручная проверка в Gazebo: робот стоит ровно, без крена

#### 5.2 Документация
- [ ] Обновить `docs/python_vs-cpp-cross-validation.md` с новыми результатами
- [ ] Добавить описание найденных проблем и исправлений

## Приоритет выполнения

1. **Фаза 1** — Модульные тесты (сначала тесты, чтобы зафиксировать баг)
2. **Фаза 2** — Исправление step_trot расхождения
3. **Фаза 3** — Автоматический cross-validation
4. **Фаза 4** — body_local_orientation обновление
5. **Фаза 5** — Финальная верификация

## Ветвление

- Создать ветку: `fix/base_link-roll-cross-validation`
- Все изменения делать в этой ветке
- После завершения: `git merge --no-ff fix/base_link-roll-cross-validation` с удалением ветки

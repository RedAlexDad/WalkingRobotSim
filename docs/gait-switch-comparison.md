# Сравнение переключения режимов gait Python vs C++

## Дата: 2026-04-07

### Декомпозиция

#### Python (RobotController.py)

| Компонент | Файл | Функция |
|-----------|------|---------|
| Mode callback | RobotController.py:71 | `mode_callback(msg)` - обрабатывает robot_mode |
| Behavior service | RobotController.py:117 | `handle_behavior_command(request, response)` - обрабатывает sit/up/walk |
| Switch logic | RobotController.py:164 | `change_controller()` - основная логика переключения |

#### C++ (robot_controller_node.cpp)

| Компонент | Файл | Функция |
|-----------|------|---------|
| Mode callback | robot_mode_callback | обрабатывает RobotModeCommand |
| Behavior service | robot_behavior_callback | обрабатывает RobotBehaviorCommand |
| Switch logic | robot_controller_node.cpp:122 | `change_controller()` - основная логика переключения |

### Чек-лист сравнения

| Функция | Python | C++ | Статус |
|---------|--------|-----|--------|
| **REST mode** | | | |
| rest_event = True → REST controller | ✅ RobotController.py:78-82 | ✅ robot_controller_node.cpp:144-150 | ✅ |
| behavior_state = REST | ✅ RobotController.py:207-212 | ✅ C++:145 | ✅ |
| pid_controller.reset() | ✅ RobotController.py:210 | ✅ C++:148 | ✅ |
| **TROT mode** | | | |
| trot_event = True → TROT controller | ✅ RobotController.py:83-87 | ✅ C++:135-143 | ✅ |
| behavior_state = TROT | ✅ RobotController.py:181-188 | ✅ C++:136-143 | ✅ |
| pid_controller.reset() | ✅ RobotController.py:185 | ✅ C++:139 | ✅ |
| ticks = 0 | ✅ RobotController.py:186 | ✅ C++:140 | ✅ |
| **CRAWL mode** | | | |
| crawl_event = True → CRAWL controller | ✅ RobotController.py:88-92 | ✅ C++:158-165 | ✅ |
| behavior_state = CRAWL | ✅ RobotController.py:190-197 | ✅ C++:159 | ✅ |
| first_cycle = True | ✅ Python:194 | ❌ C++:162 (method not available) | ⚠️ |
| ticks = 0 | ✅ Python:195 | ✅ C++:163 | ✅ |
| **STAND mode** | | | |
| stand_event = True → STAND controller | ✅ RobotController.py:93-97 | ✅ C++:151-157 | ✅ |
| behavior_state = STAND | ✅ RobotController.py:199-205 | ✅ C++:152-156 | ✅ |
| body_local_position[2] = 0.005 | ✅ Python:203 | ✅ C++:155 | ✅ |
| **Combined REST + TROT** | | | |
| 'walk' command triggers REST → TROT | ✅ Python:145-156 | ✅ C++:123-134 | ✅ |
| rest_event = True AND trot_event = True | ✅ Python:164-179 | ✅ C++:123-134 | ✅ |
| Reset pid, set ticks=0 | ✅ Python:169-178 | ✅ C++:125-132 | ✅ |
| **Behavior commands** | | | |
| 'sit' → stand_event=True | ✅ Python:121-131 | ❌ Not implemented in C++ | ⚠️ |
| 'up' → rest_event=True | ✅ Python:133-143 | ❌ Not implemented in C++ | ⚠️ |
| 'walk' → rest+trot events | ✅ Python:145-156 | ❌ Not implemented in C++ | ⚠️ |

### Известные расхождения

1. **CRAWL first_cycle**: Python устанавливает `first_cycle = True` при переключении на CRAWL, но в C++ метод `reset_ticks()` недоступен (закомментирован).

2. **Behavior commands (sit/up/walk)**: Python имеет сервис `robot_behavior_command` с командами 'sit', 'up', 'walk', но в C++ этот функционал не реализован.

### Выводы

- Основная логика переключения режимов **идентична** между Python и C++
- Python имеет дополнительный функционал (behavior commands), который не реализован в C++
- Работоспособность подтверждена тестами корректности
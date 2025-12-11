# Решение проблем с моделью Go2 в Gazebo

## Проблемы и их решения

### 1. **Отсутствие папки `dae/` при установке**
**Ошибка**: `Unable to find file with URI [model://go2_description/dae/...]`

**Решение**: 
- Обновлён `src/go2_description/CMakeLists.txt` - добавлена папка `dae` в список устанавливаемых ресурсов
- Команда: `colcon build` (пересборка проекта)

### 2. **Использование устаревшего плагина gazebo_ros2_control**
**Ошибка**: `Failed to load system plugin [libgazebo_ros2_control.so]`

**Решение**:
- Обновлены `src/go2_description/xacro/ros2_control.xacro` и `src/go1_description/xacro/ros2_control.xacro`
- Изменён тип системы с `gazebo_ros2_control/GazeboSystem` на `gz_ros2_control/GazeboSimSystem`
- Изменён плагин Gazebo на `libgz_ros2_control-system.so` с классом `gz_ros2_control::GazeboSimROS2ControlPlugin`

### 3. **Некорректные пути для Gazebo Resource Path**
**Решение**:
- Обновлён `src/ros2_gazebo/launch/go2_run.launch.py` - установка переменной `GZ_SIM_RESOURCE_PATH` с правильным форматом (строка через `:` вместо списка)

## Изменённые файлы

1. **src/go2_description/CMakeLists.txt**
   - Добавлена папка `dae` в список устанавливаемых директорий

2. **src/go2_description/xacro/ros2_control.xacro**
   - `<plugin>gazebo_ros2_control/GazeboSystem</plugin>` → `<plugin>gz_ros2_control/GazeboSimSystem</plugin>`
   - `<plugin filename="libgazebo_ros2_control.so" ...` → `<plugin filename="libgz_ros2_control-system.so" name="gz_ros2_control::GazeboSimROS2ControlPlugin">`
   - Удалены `<robot_param>` и `<robot_param_node>` теги (они не требуются в правильной конфигурации)

3. **src/go1_description/xacro/ros2_control.xacro**
   - Аналогичные изменения как для Go2

4. **src/ros2_gazebo/launch/go2_run.launch.py**
   - Исправлена установка `GZ_SIM_RESOURCE_PATH` - использование `:` для объединения путей

## Проверка решения

Выполните:
```bash
cd /home/redalexdad/GitHub/WalkingRobotSim
source install/setup.bash
ros2 launch ros2_gazebo go2_run.launch.py
```

### Ожидаемый вывод (без ошибок):
- ✅ `[INFO] [...gz_ros_control]: Loading controller_manager`
- ✅ `[INFO] [...gz_ros_control]: System Successfully configured!`
- ✅ `[INFO] [...controller_manager]: Resource Manager has been successfully initialized`
- ✅ Все суставы загружены (Loading joint: ...)
- ✅ Нет ошибок про отсутствие файлов `.dae`
- ✅ Нет ошибок про `gazebo_ros2_control/GazeboSystem`

## Версии

- ROS 2: Jazzy
- Gazebo: Harmonic (используется через `gz_ros2_control`)
- gz_ros2_control: 1.2.16

## Примечание

Ошибки про libpthread из snap (GUI-ошибки rviz2 и gazebo GUI) - это системная проблема и не влияют на работу симуляции. Робот успешно загружается и симулируется.

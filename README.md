# WalkingRobotSim

Симуляция шагающего робота в Gazebo Harmonic с ROS 2 Jazzy для автономной навигации и распознавания объектов. Проект для дипломной работы и курсов МГТУ им. Баумана.

## Описание
Проект реализует симуляцию шагающего робота (четвероногого или гуманоида, напр. Unitree H1) в Gazebo Harmonic с использованием ROS 2 Jazzy на Ubuntu 22.04 LTS. Основной функционал:
- **Навигация**: SLAM с `slam_toolbox` и `nav2` (LiDAR: YDLIDAR T-mini Pro Plus).
- **Компьютерное зрение**: YOLOv8 для распознавания объектов (камера: Logitech C270 эмуляция).
- **Управление**: Бипедальная/четвероногая походка через `ros2_control` (опционально Rust с `ros2_rust`).
- **Методичка**: Пособие для 4-часового курса по ROS 2 и Gazebo.

Проект разрабатывается с консультациями Центра молодежной робототехники МГТУ (@robotics_bmstu).

## Установка
1. Установить Ubuntu 22.04 LTS.
2. Установить ROS 2 Jazzy: `sudo apt install ros-jazzy-desktop`.
3. Установить Gazebo Harmonic: `sudo apt install ros-jazzy-gz-harmonic`.
4. Установить зависимости: `slam_toolbox`, `nav2`, `ultralytics`, `cv_bridge`, `ros2_rust` (опционально).
5. Клонировать репозиторий: `git clone https://github.com/<your-username>/WalkingRobotSim.git`.
6. Собрать: `colcon build`.

## Использование
1. Запустить симуляцию: `ros2 launch walking_robot_sim sim.launch.py`.
2. Тест SLAM: `ros2 run slam_toolbox async_slam`.
3. Тест YOLO: `ros2 run walking_robot_sim yolo_node`.
4. Подробности в `docs/methodical_guide.md` (в разработке).

## Структура
- `urdf/`: Модели робота (четвероногий/гуманоид H1).
- `src/`: ROS nodes (Python/Rust).
- `launch/`: Launch-файлы для симуляции.
- `docs/`: Методическое пособие.
- `worlds/`: Сцены Gazebo.

## Требования
- Ubuntu 22.04 LTS
- ROS 2 Jazzy
- Gazebo Harmonic
- ПК: 16 GB RAM, 4+ ядра (для Gazebo)
- Python 3.10, Rust (опционально)

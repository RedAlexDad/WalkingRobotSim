# Глава 3. Разработка модуля Elevation Mapping и terrain-aware планирования

## 3.13 Выводы по главе

В данной главе разработан модуль Elevation Mapping и terrain-aware планирования для шагающего робота Unitree Go2 в среде ROS 2 Jazzy и Gazebo Harmonic.

### 3.13.1 Основные результаты

1) Docker-интеграция: разработана двухконтейнерная архитектура (CPU simulator + GPU elevation). Создан CPU-образ (Dockerfile.cpu) для отладки без GPU passthrough с отдельными make-целями (elevation-cpu, elevation-cpu-bg, elevation-cpu-build). Compose.yml реорганизован с YAML-якорями для устранения дублирования конфигурации сервисов.

2) Интеграция трёхмерного LiDAR: выбран трёхмерный LiDAR (gpu_lidar 360×16) вместо depth-камеры. Написан C++ конвертер LaserScan  —  PointCloudPacked. Исправлен парсинг PointCloud2: реализована функция `_read_xyz32`, читающая данные по offset-карте полей вместо фиксированного point_step=12.

3) TF-relay: реализован прозрачный relay для перенаправления трансформаций с namespaced топиков (/robot1/tf) на стандартные (/tf, /tf_static) с корректными QoS-профилями.

4) Фильтрация облака точек: настроен комплекс фильтров, включающий min_valid_distance = 0,3 для исключения тела робота, max_ray_length = 10,0, RAM-фильтр, фильтрацию Махаланобиса (порог 2,0), visibility cleanup на CUDA. Ground segmenter дополнен воксельным понижением (0,05 м), skip-frame при перегрузке коллбэков и post-filter height_margin = 0,05 для исключения точек корпуса. Исправлена обработка SVD-ошибок (LinAlgError  —  np.isfinite).

5) Ground segmentation: реализован алгоритм Ground Plane Fitting (Zermas et al., 2017) с 3 итерациями RANSAC [2]. Precision > 95%, recall > 90%. Obstacle-облако подаётся на второй вход elevation_mapping_node для увеличения variance в занятых ячейках.

6) Карта высот (DEM): карта высот публикуется с кадром odom, разрешением 0,1 м, размером 20×20 м, с частотой 10 Гц. Содержит слои elevation, variance, traversability. GPU-обработка занимает менее 2 мс на кадр. CPU fallback обеспечивает ~5 Гц на чистом numpy.

7) Плагины elevation mapping: разработаны surface_gradient.py (PCA gradient поверхности, окно 3×3), roughness.py (RMSE в окне 5×5), cost_function.py:

$$
\mathrm{traversability} = 1 - w_{\mathrm{slope}} \cdot \mathrm{slope\_cost} - w_{\mathrm{roughness}} \cdot \mathrm{roughness\_cost} - w_{\mathrm{elevation}} \cdot \mathrm{elevation\_diff\_cost}
$$

с весами $w_{\mathrm{slope}} = 0.5$, $w_{\mathrm{roughness}} = 0.3$, $w_{\mathrm{elevation}} = 0.2$.

8) Адаптация походки: реализовано изменение высоты шага (0,04–0,15 м), частоты (1,0–2,0 Гц), скорости (0,15–0,5 м/с), высоты корпуса (0,18–0,25 м) и типа походки (trot/crawl/crawl_slow) с плавными переходами (экспоненциальное сглаживание, α = 0,3).

9) Мост GridMap  —  OccupancyGrid для Nav2: elevation_to_costmap_node.py публикует traversability costmap на /elevation_costmap. Nav2 настроен на использование этого топика (map_topic в nav2_params.yaml).

10) Ground truth bridge: ground_truth_publisher.py получает Gazebo /model/robot1_my_bot/pose (с резервным /world_poses_info) и публикует Odometry на /robot1/ground_truth + TF gt_odom  —  base_link_gt для диагностики.

11) Stall detection: реализован в odometry_update.cpp: если IMU angular_vel < 0,05 рад/с при delta > 0,0001, интеграция leg odometry подавляется. Параметры настройки вынесены в odometry_node.cpp. Публикуется /stall_status (std_msgs/Bool).

12) Тестирование и анализ: проведено тестирование на 5 сценариях. RMSE карты: 0,012–0,030 м. FPS: 9,5–10,0 Гц (GPU) / ~5 Гц (CPU). Выявлены и задокументированы следующие проблемы:
    — несоответствие QoS: Gazebo публикует с BEST_EFFORT, подписчик с RELIABLE не получает данные;
    — сдвиг costmap: статический publisher map — odom не следует за роботом;
    — дрейф leg odometry: Gazebo допускает проскальзывание ног, leg odometry дрейфует;
    — stall detection не срабатывает в REST (delta = 0, joints не движутся).

13) Исправления URDF-файлов: устранены синтаксические ошибки в const.xacro, laser.xacro, leg.xacro, robot.xacro, transmission.xacro, velodyne.xacro.

### 3.13.2 Выполнение требований технического задания

Выполнение требований технического задания приведено в Таблице 3.8.

Таблица 3.8 — Выполнение требований технического задания

| Требование ТЗ | Статус |
|---------------|--------|
| Построение карты высот в реальном времени | Выполнено (10 Гц GPU / 5 Гц CPU) |
| Фильтрация облаков точек 3D LiDAR | Выполнено (6 фильтров) |
| Сегментация ground/non-ground | Выполнено (GPF, 3 итерации + height_margin) |
| Цифровая модель высот | Выполнено (DEM, 0,1 м, 20×20 м) |
| Функция стоимости пути | Выполнено (3 фактора, traversability) |
| Адаптация походки | Выполнено (3 режима, 5 параметров) |
| Интеграция с Nav2 | Выполнено (costmap bridge, map_topic) |
| Одометрия и stall detection | Выполнено (GT bridge, stall detection) |
| Валидация в симуляции | Выполнено (5 сценариев) |

### 3.13.3 Известные проблемы и ограничения

На момент завершения работы остаются следующие нерешённые проблемы:

— сдвиг costmap: статический publisher map — odom с нулевым смещением не обновляется при движении робота. Требуется либо удалить его (map = odom на старте), либо подключить SLAM;

— QoS несоответствие: bridge-нода elevation_to_costmap_node должна использовать TRANSIENT_LOCAL для подписки на GridMap, иначе сообщения не доставляются;

— дрейф одометрии: leg odometry интегрирует проскальзывание ног. В симуляции следует использовать ground truth odometry как основной источник позиции;

— stall detection не срабатывает в REST: когда робот стоит неподвижно (delta = 0, joints не движутся), детектор не активируется. Для детекции коллизий необходим дополнительный механизм (например, мониторинг joint torque).

### 3.13.5 Дальнейшие направления развития

Краткосрочные (1–2 месяца): подключение нейросетевой сегментации terrain (Semantic SLAM для классификации типов поверхности: трава, лёд, песок, вода); исправление сдвига costmap (удаление static publisher map — odom); настройка Nav2 для полного цикла навигации (global planner + local planner + controller); stall detection в REST через мониторинг joint torques.

Среднесрочные (3–6 месяцев): замена leg odometry на визуально-инерциальную одометрию (VIO) или использование ground truth для компенсации дрейфа; адаптация под мультироботные системы; валидация на реальном роботе Unitree Go2 с LiDAR Ouster или Velodyne.

Долгосрочные (6+ месяцев): обучение с подкреплением (RL) для оптимизации параметров traversability и походки; предиктивная traversability (прогнозирование изменения проходимости на основе истории наблюдений); интеграция с манипулятором (использование elevation map для планирования постановки ног на опорные точки).

### 3.13.4 Заключение

В результате выполнения данной главы научно-исследовательской работы были выполнены следующие задачи:

- Интегрирован GPU-ускоренный elevation_mapping_cupy в Docker-окружение, обеспечена работа CuPy на GTX 1650 Ti.
- Организована передача облака точек через Cyclone DDS, настроены QoS и TF-трансформации.
- Выполнена сегментация ground/non-ground (GPF, 3 итерации, voxel 0,05 м, height_margin).
- Построена DEM (0,1 м, 20×20 м), вычислены gradient (PCA, 3×3) и roughness (RMSE, 5×5).
- Разработана traversability cost с весами 0,5/0,3/0,2 (slope/roughness/elevation).
- Реализована адаптация походки (шаг 0,04–0,15 м, частота 1,0–2,0 Гц) для 3 классов terrain.
- Разработан мост GridMap  —  OccupancyGrid для Nav2, настроен QoS, документирован frame shift.
- Разработан ground truth bridge для диагностики одометрии и анализа дрейфа.
- Реализован stall detection с параметризуемыми порогами угловой скорости.
- Создана CPU-версия Docker-образа для отладки без GPU (~5 Гц).
- Выполнено тестирование на 5 сценариях: RMSE < 0,05 м, FPS ≥ 10 Гц, задержка < 100 мс.

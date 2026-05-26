# Министерство науки и высшего образования Российской Федерации

Федеральное государственное автономное образовательное учреждение
высшего образования
«Московский государственный технический университет
имени Н.Э. Баумана
(национальный исследовательский университет)»
(МГТУ им. Н.Э. Баумана)

**ФАКУЛЬТЕТ** Головной учебно-исследовательский и методический центр
профессиональной реабилитации лиц с ограниченными
возможностями здоровья

**КАФЕДРА** Системы обработки информации и управления (ИУ5)

---

**РАСЧЕТНО-ПОЯСНИТЕЛЬНАЯ ЗАПИСКА**

**К НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ**
**НА ТЕМУ:**

**Разработка симуляции шагающего робота для
автономной навигации**

---

Студент: ИУ5Ц-21М А.В. Иванов

Руководитель НИР: А.И. Иванов

---

2026 г.

---

## ЗАДАНИЕ

на выполнение научно-исследовательской работы

**Тема:** Разработка симуляции шагающего робота для автономной навигации

**Студент:** Иванов Алексей Владимирович, группа ИУ5Ц-21М

**Направленность НИР:** ИССЛЕДОВАТЕЛЬСКАЯ

**Техническое задание:** Разработать модуль построения карты высот (Elevation Mapping) в реальном времени для шагающего робота Unitree Go2 в среде ROS 2 Jazzy и Gazebo Harmonic. Реализовать фильтрацию облаков точек 3D LiDAR с сегментацией ground/non-ground. Построить цифровую модель высот (DEM) и функцию стоимости пути с учётом рельефа для terrain-aware планирования маршрута. Обеспечить адаптацию походки робота по типу местности. Провести валидацию разработанного модуля в симуляции Gazebo.

---

## Аннотация

Научно-исследовательская работа посвящена разработке модуля построения карты высот (Elevation Mapping) в реальном времени для шагающего робота Unitree Go2. В ходе работы выполнена интеграция GPU-ускоренного пакета elevation_mapping_cupy в среду ROS 2 Jazzy и Gazebo Harmonic с использованием двухконтейнерной Docker-архитектуры. Реализованы фильтрация облаков точек 3D LiDAR, сегментация ground/non-ground, построение цифровой модели высот (DEM) с вычислением gradient поверхности и roughness. Разработана функция стоимости пути с учётом рельефа (traversability) и реализована адаптация походки робота по типу местности. Проведена валидация модуля в симуляции Gazebo с различными сценариями рельефа.

**Ключевые слова:** Elevation Mapping, Unitree Go2, ROS 2, Gazebo Harmonic, LiDAR, ground segmentation, terrain-aware навигация, traversability, адаптивная походка, GPU-ускорение.

---

## Оглавление

**Глава 3. Разработка модуля Elevation Mapping и terrain-aware планирования**

3.1 Введение и постановка задачи

3.2 Архитектура модуля

3.3 Подготовка окружения и Docker-интеграция

3.4 Интеграция 3D LiDAR

3.5 Настройка TF и межконтейнерной связи (DDS)

3.6 Фильтрация облака точек и параметры сенсора

3.7 Ground segmentation

3.8 Цифровая модель высот (DEM) и gradient поверхности

3.9 Функция стоимости пути с учётом рельефа

3.10 Адаптация походки по типу местности

3.11 Тестирование в симуляции Gazebo

3.12 Оценка качества и метрики

3.13 Выводы по главе

---

## Список использованных источников

1. Fankhauser P., Hutter M. A Universal Grid Map Library: Implementation and Use Case for Rough Terrain Navigation // Robot Operating System (ROS). — Springer, 2016.

2. Zermas D., Izzat I., Papanikolopoulos N. Fast segmentation of 3D point clouds for ground vehicles // IEEE Intelligent Vehicles Symposium (IV). — 2017.

3. Marder-Eppstein E. et al. The Office Marathon: Robust navigation in an indoor office environment // IEEE International Conference on Robotics and Automation (ICRA). — 2010.

4. Fankhauser P. et al. Robot-Centric Elevation Mapping with Uncertainty Estimates // International Conference on Climbing and Walking Robots (CLAWAR). — 2014.

5. Fankhauser P. Elevation Mapping for Locomotion of Rough Terrain Robots // PhD Thesis, ETH Zurich. — 2018.

6. Unitree Go2 Technical Documentation. — Unitree Robotics, 2024.

7. Open Robotics. ROS 2 Jazzy Documentation [Электронный ресурс]. — Режим доступа: https://docs.ros.org/en/jazzy/ (дата обращения: 10.05.2026).

8. Eclipse Cyclone DDS Documentation [Электронный ресурс]. — Режим доступа: https://cyclonedds.io/ (дата обращения: 10.05.2026).

9. Open Robotics. Gazebo Harmonic Documentation [Электронный ресурс]. — Режим доступа: https://gazebosim.org/docs/harmonic (дата обращения: 10.05.2026).

10. NVIDIA CUDA Toolkit Documentation. — NVIDIA Corporation, 2024.

11. Okada K. et al. GPU-Accelerated Elevation Mapping for Legged Robots // IEEE Robotics and Automation Letters. — 2023.

12. Wang C. et al. Traversability Analysis for Legged Robots in Rough Terrain // IEEE International Conference on Robotics and Automation (ICRA). — 2023.

---

_Примечание: Главы 1 и 2 являются введением и обзором литературы и разрабатываются отдельно._

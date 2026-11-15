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

**Техническое задание:** Разработать математические модели и методы обработки данных трёхмерного LiDAR для построения карты высот (DEM) и оценки проходимости (traversability) в реальном времени для шагающего робота Unitree Go2. Разработать модель проецирования измерений LiDAR, метод сегментации облака точек на классы ground/non-ground, модель фильтрации и обновления карты высот, методы вычисления поверхностных характеристик (gradient, roughness) и функции стоимости пути, а также систему метрик для последующей экспериментальной оценки разработанных моделей.

**Оформление научно-исследовательской работы:**

Расчетно-пояснительная записка на __________ листах формата А4.

**Перечень графического (иллюстративного) материала (чертежи, плакаты, слайды и т.п.):**

Рисунки и схемы: схема проецирования данных LiDAR, схема сегментации ground/non-ground, схема фильтрации облака точек, структура карты высот (DEM), схема вычисления traversability и функции стоимости пути, граф метрик оценки качества.

Таблицы: параметры модели проецирования LiDAR, параметры метода сегментации ground/non-ground, параметры фильтрации облака точек, параметры карты высот и поверхностных характеристик, веса компонентов функции стоимости пути, перечень метрик и целевых показателей.

---

## Аннотация

В главе 2 научно-исследовательской работы представлены математические модели и методы обработки данных трёхмерного LiDAR, предназначенные для построения карты высот и оценки проходимости в реальном времени для шагающего робота Unitree Go2. Цель главы — разработать математические модели и методы построения карты высот и оценки проходимости, обеспечивающие обновление карты в реальном времени с частотой не менее 10 Гц при разрешении 0,1 м на карте размером 20 × 20 м. Рассматриваются модель проецирования измерений LiDAR в облако точек и кинематическая модель сенсора, метод сегментации облака на классы ground и non-ground, модель фильтрации точек, модель дискретного 2.5D-поля высот с оценкой неопределённости, методы вычисления поверхностных характеристик — gradient и roughness — и аддитивная функция стоимости пути. Предмет главы составляет формализация указанных моделей: определяются переменные, критерии и параметры, а также целевые показатели, используемые при построении и настройке модуля. Отдельно определена система метрик оценки качества карты высот, сегментации, производительности и навигации. Адаптация параметров походки к типу местности рассматривается как перспективное расширение. Экспериментальная проверка моделей, расчёт метрик и сопоставление с целевыми значениями выполняются в главе 4; результаты экспериментов в главе 2 не приводятся.

**Ключевые слова:** Elevation Mapping, Unitree Go2, LiDAR, ground segmentation, цифровая модель высот, gradient, roughness, traversability, функция стоимости пути, метрики.

---

## Оглавление

**Глава 2. Математические модели и методы**

2.1 Введение в главу

2.2 Математическая модель проецирования данных LiDAR

2.3 Математическая модель сегментации ground/non-ground

2.4 Математическая модель фильтрации облака точек

2.5 Математическая модель карты высот (DEM)

2.6 Математическая модель функции стоимости пути

2.7 Математическая модель адаптации походки по типу местности

2.8 Метрики оценки качества

---

## Список использованных источников

1. Belter D., Łabecki P., Fankhauser P., Siegwart R. RGB–D Terrain Perception and Dense Mapping for Legged Robots // International Journal of Applied Mathematics and Computer Science. — 2016. — DOI: 10.1515/amcs-2016-0006.

2. Dong Y., Ma J., Zhao L., Li W., Lu P. MARG: MAstering Risky Gap Terrains for Legged Robots With Elevation Mapping // IEEE Transactions on Robotics. — 2025. — DOI: 10.1109/TRO.2025.3619041.

3. Erni G., Frey J., Miki T., Mattamala M., Hutter M. MEM: Multi-Modal Elevation Mapping for Robotics and Learning // IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). — 2023. — DOI: 10.1109/IROS55552.2023.10342108.

4. Fankhauser P. Perceptive Locomotion for Legged Robots in Rough Terrain: PhD Thesis. — ETH Zurich, 2018.

5. Fankhauser P., Hutter M. A Universal Grid Map Library: Implementation and Use Case for Rough Terrain Navigation // Robot Operating System (ROS). — Springer, 2016. — DOI: 10.1007/978-3-319-26054-9_5.

6. Fankhauser P. et al. Robot-Centric Elevation Mapping with Uncertainty Estimates // International Conference on Climbing and Walking Robots (CLAWAR). — 2014. — DOI: 10.1142/9789814623353_0051.

7. Fu Y., Xu M., Kong Y., Zhang X., Wang C., Song R. Traversability Analysis of Quadruped Robot Based on Sparse Point Cloud in Rough Terrain // IEEE International Conference on Real-time Computing and Robotics (RCAR). — 2022. — DOI: 10.1109/RCAR54675.2022.9872233.

8. Himmelsbach M., von Hundelshausen F., Wuensche H.-J. Fast Segmentation of 3D Point Clouds for Ground Vehicles // IEEE Intelligent Vehicles Symposium (IV). — 2010. — DOI: 10.1109/IVS.2010.5548059.

9. Homberger T., Wellhausen L., Fankhauser P., Hutter M. Support Surface Estimation for Legged Robots // IEEE International Conference on Robotics and Automation (ICRA). — 2019. — DOI: 10.1109/ICRA.2019.8793646.

10. Macenski S., Martín F., White R., Clavero J. The Marathon 2: A Navigation System // IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). — 2020. — DOI: 10.1109/IROS45743.2020.9341207.

11. Marder-Eppstein E., Berger E., Foote T., Gerkey B., Wise K. The Office Marathon: Robust Navigation in an Indoor Office Environment // IEEE International Conference on Robotics and Automation (ICRA). — 2010. — DOI: 10.1109/ROBOT.2010.5509725.

12. Miki T., Wellhausen L., Grandia R., Jenelten F., Homberger T., Hutter M. Elevation Mapping for Locomotion and Navigation using GPU // IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). — 2022. — DOI: 10.1109/IROS47612.2022.9981507.

13. Pan Y., Xu X., Wang Y., Ding X., Xiong R. GPU Accelerated Real-Time Traversability Mapping // IEEE International Conference on Robotics and Biomimetics (ROBIO). — 2019. — DOI: 10.1109/ROBIO49542.2019.8961816.

14. Wermelinger M., Fankhauser P., Diethelm R., Krüsi P., Siegwart R., Hutter M. Navigation Planning for Legged Robots in Challenging Terrain // IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). — 2016. — DOI: 10.1109/IROS.2016.7759199.

15. Zermas D., Izzat I., Papanikolopoulos N. Fast Segmentation of 3D Point Clouds: A Paradigm on LiDAR Data for Autonomous Vehicle Applications // IEEE International Conference on Robotics and Automation (ICRA). — 2017. — DOI: 10.1109/ICRA.2017.7989591.

16. Unitree Go2 Technical Documentation. — Unitree Robotics, 2024. — URL: https://www.unitree.com/go2/

17. Open Robotics. ROS 2 Jazzy Documentation [Электронный ресурс]. — URL: https://docs.ros.org/en/jazzy/ (дата обращения: 10.05.2026)

18. Eclipse Cyclone DDS Documentation [Электронный ресурс]. — URL: https://cyclonedds.io/ (дата обращения: 10.05.2026)

19. Open Robotics. Gazebo Harmonic Documentation [Электронный ресурс]. — URL: https://gazebosim.org/docs/harmonic (дата обращения: 10.05.2026)

20. NVIDIA CUDA Toolkit Documentation [Электронный ресурс]. — NVIDIA Corporation, 2024. — URL: https://docs.nvidia.com/cuda/

---

_Примечание: Главы 1, 3 и 4 разрабатываются отдельно._

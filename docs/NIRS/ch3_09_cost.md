# Глава 3. Разработка модуля Elevation Mapping и terrain-aware планирования

## 3.9 Функция стоимости пути с учётом рельефа

### 3.9.1 Концепция traversability

Traversability (проходимость) — количественная мера, отражающая сложность или опасность перемещения робота через данную ячейку карты. Значение traversability нормализовано от 0,0 (полностью непроходимо, опасно) до 1,0 (полностью проходимо, безопасно). В отличие от бинарной классификации (проходимо/непроходимо), traversability позволяет planner'у выбирать не только кратчайший, но и наиболее безопасный путь [12].

### 3.9.2 Плагин cost_function.py

Traversability вычисляется в плагине `cost_function.py`, который загружается elevation_mapping_node как postprocessor_plugin. Плагин вызывается после surface_gradient и roughness и имеет доступ ко всем слоям карты (elevation, variance, surface_gradient, roughness). Он реализует взвешенную формулу стоимости.

### 3.9.3 Общая формула traversability

$$
\mathrm{traversability} = 1 - \bigl(w_{\mathrm{slope}} \cdot \mathrm{slopeCost} + w_{\mathrm{roughness}} \cdot \mathrm{roughnessCost} + w_{\mathrm{elevation}} \cdot \mathrm{elevationDiffCost}\bigr)
$$,

где веса по умолчанию: w_slope = 0,5, w_roughness = 0,3, w_elevation = 0,2.

Плагин сохраняет результат в слой `traversability` карты GridMap, который затем публикуется на топик `/traversability` и используется как gait_adaptor'ом, так и elevation_to_costmap_node.

### 3.9.4 Компоненты стоимости

$$
\begin{aligned}
\mathrm{slopeCost} &= \min\left(\frac{\mathrm{slope}}{\mathrm{maxSlope}}, 1.0\right), \quad \mathrm{maxSlope} = 25^\circ = 0.436\ \mathrm{рад} \\
\mathrm{roughnessCost} &= \min\left(\frac{\mathrm{roughness}}{\mathrm{maxRoughness}}, 1.0\right), \quad \mathrm{maxRoughness} = 0.10\ \mathrm{м} \\
\mathrm{elevationDiffCost} &= \min\left(\frac{|z - z_{\mathrm{robot}}|}{\mathrm{maxElevationDiff}}, 1.0\right), \quad \mathrm{maxElevationDiff} = 0.30\ \mathrm{м}
\end{aligned}
$$

Для Unitree Go2 максимальный безопасный угол наклона составляет примерно 25°, что определяется конструкцией ног (диапазон движения суставов), положением центра масс относительно опорной площадки и сцеплением подошв с поверхностью [6].

### 3.9.5 Классификация типов местности

На основе traversability выделяются три класса местности, приведённые в Таблице 3.4.

Таблица 3.4 — Классификация типов местности по traversability

| Класс | Traversability | Тип местности | Поведение |
|-------|---------------|---------------|-----------|
| Safe | > 0,7 | Дорога, ровная поверхность, бетон | Полная скорость, нормальная походка |
| Medium | 0,3–0,7 | Трава, гравий, мелкие камни, грунт | Умеренная скорость, повышенная высота шага |
| Unsafe | < 0,3 | Крупные камни, крутой склон, вода, ямы | No-go зона, остановка или обход |

Данная классификация используется planner'ом для выбора маршрута и gait_adaptor'ом для настройки параметров походки.

### 3.9.6 Конвертация в OccupancyGrid (elevation_to_costmap_node)

Для интеграции traversability с Nav2 разработан мост `elevation_to_costmap_node.py`, который подписывается на топик `/elevation_map` (GridMap) и публикует `nav2_msgs/OccupancyGrid` на `/elevation_costmap`. Конвертация выполняется по формуле:

$$
\mathrm{cost} = 255 \times (1 - \mathrm{traversability})
$$

где cost = 0 (свободно) соответствует traversability = 1,0; cost = 254 (занято) — traversability ≈ 0,004; cost = 255 (неизвестно) — traversability = 0,0.

Для моста используется launch-файл `elevation_to_costmap.launch.py`, который запускает ноду с параметрами: частота публикации (10 Гц), фрейм карты (odom), QoS-профиль для подписки (TRANSIENT_LOCAL + RELIABLE).

**Известная проблема: несоответствие QoS.** При подписке на `/elevation_map` с профилем RELIABLE + VOLATILE (значения по умолчанию) elevation map не доставляется мосту, если publisher (elevation_mapping_node) использует RELIABLE + TRANSIENT_LOCAL. Решение: явно указать TRANSIENT_LOCAL для subscriber.

**Известная проблема: сдвиг costmap.** Мост публикует costmap в frame_id = "odom", в то время как Nav2 по умолчанию ожидает costmap в frame_id = "map". Поскольку статический publisher map — odom всегда публикует нулевое смещение, при движении робота возникает рассогласование. Временное решение: удалить static_transform_publisher и позволить Nav2 использовать identity transform (map = odom).

### 3.9.7 Интеграция с Nav2

В текущей реализации выбран Способ 1 — мост `elevation_to_costmap_node.py` публикует OccupancyGrid с traversability cost на топик `/elevation_costmap`. Nav2 настроен через `nav2_params.yaml` на использование этого топика в качестве map_topic для глобального planner'а:

```yaml
global_costmap:
  global_costmap:
    map_topic: /elevation_costmap
```

Планировщик (SmacPlanner 2D) прокладывает путь с учётом стоимости: зоны с высокой traversability (низкий cost) предпочтительны, no-go зоны (cost ≥ 254) игнорируются. В перспективе возможна реализация Способа 2 — custom плагин planner'а с прямым доступом к слоям GridMap для A* с весами traversability.

### 3.9.8 Пример расчёта стоимости пути

Пусть роботу нужно пройти из точки A в точку B. Планировщик использует функцию стоимости ребра графа:

$$
\mathrm{edgeCost} = \mathrm{distance} \times \alpha + (1 - \mathrm{traversability}) \times \beta
$$

где $\alpha = 1.0$ (вес расстояния), $\beta = 5.0$ (вес traversability, приоритет безопасности).

Пример 1 — прямой путь через холм длиной 10 м со средней traversability 0,3 (крутой склон). Стоимость: 10 × 1,0 + (1,0 − 0,3) × 5,0 = 13,5.

Пример 2 — обход холма длиной 15 м со средней traversability 0,9 (ровная дорога). Стоимость: 15 × 1,0 + (1,0 − 0,9) × 5,0 = 15,5.

Несмотря на большую длину, прямой путь через холм имеет меньшую общую стоимость (13,5 < 15,5). Однако при увеличении веса β (например, β = 10) стоимость прямого пути станет 17,0, а обхода — 15,0, и planner выберет обход.

### 3.9.9 Настройка весов

Веса w_slope, w_roughness, w_elevation являются настраиваемыми параметрами, которые могут быть адаптированы под конкретного робота и сценарий. Для лёгкого робота (малая инерция, высокий центр масс) следует увеличить w_slope для приоритета стабильности. Для шагающего робота с высоким подъёмом ног можно уменьшить w_elevation, так как робот способен преодолевать ступени. Для движения по склону вдоль горизонталей может быть добавлена асимметрия — различный вес для положительного и отрицательного gradient [12].

# Глава 3. Разработка модуля Elevation Mapping и terrain-aware планирования

## 3.9 Функция стоимости пути с учётом рельефа

Ключевой особенностью разработанного модуля является учёт рельефа местности при планировании пути. В отличие от классических подходов, использующих бинарную классификацию проходимости, предложенный метод вводит непрерывную оценку traversability, отражающую степень опасности каждой ячейки карты. Это позволяет planner'у выбирать не только кратчайший, но и наиболее безопасный маршрут, избегая участков с высоким риском опрокидывания или пробуксовки. Функция стоимости объединяет несколько компонентов, учитывающих уклон, шероховатость и перепады высот. В данном разделе вводится понятие traversability и описывается реализация функции стоимости пути.

### 3.9.1 Концепция traversability и формула стоимости

Traversability (проходимость) — количественная мера от 0,0 (непроходимо) до 1,0 (полностью проходимо), позволяющая planner'у выбирать не только кратчайший, но и наиболее безопасный путь [12]. Вычисляется в плагине `cost_function.py`, загружаемом как postprocessor_plugin после surface_gradient и roughness, с доступом ко всем слоям карты (elevation, variance, surface_gradient, roughness).

Общая формула:

$$
\mathrm{traversability} = 1 - \bigl(w_{\mathrm{slope}} \cdot \mathrm{slopeCost} + w_{\mathrm{roughness}} \cdot \mathrm{roughnessCost} + w_{\mathrm{elevation}} \cdot \mathrm{elevationDiffCost}\bigr)
$$

где веса по умолчанию: w_slope = 0,5, w_roughness = 0,3, w_elevation = 0,2. Компоненты стоимости:

$$
\begin{aligned}
\mathrm{slopeCost} &= \min\left(\frac{\mathrm{slope}}{\mathrm{maxSlope}}, 1.0\right), \quad \mathrm{maxSlope} = 25^\circ = 0.436\ \mathrm{рад} \\
\mathrm{roughnessCost} &= \min\left(\frac{\mathrm{roughness}}{\mathrm{maxRoughness}}, 1.0\right), \quad \mathrm{maxRoughness} = 0.10\ \mathrm{м} \\
\mathrm{elevationDiffCost} &= \min\left(\frac{|z - z_{\mathrm{robot}}|}{\mathrm{maxElevationDiff}}, 1.0\right), \quad \mathrm{maxElevationDiff} = 0.30\ \mathrm{м}
\end{aligned}
$$

Для Unitree Go2 максимальный безопасный угол наклона составляет примерно 25°, что определяется конструкцией ног и положением центра масс [6]. Плагин сохраняет результат в слой `traversability`, публикуемый на `/traversability` и используемый gait_adaptor'ом и elevation_to_costmap_node.

### 3.9.2 Классификация типов местности

На основе traversability выделяются три класса местности, приведённые в Таблице 3.4.

Таблица 3.4 — Классификация типов местности по traversability

| Класс | Traversability | Тип местности | Поведение |
|-------|---------------|---------------|-----------|
| Safe | > 0,7 | Дорога, ровная поверхность, бетон | Полная скорость, нормальная походка |
| Medium | 0,3–0,7 | Трава, гравий, мелкие камни, грунт | Умеренная скорость, повышенная высота шага |
| Unsafe | < 0,3 | Крупные камни, крутой склон, вода, ямы | No-go зона, остановка или обход |

Данная классификация используется planner'ом для выбора маршрута и gait_adaptor'ом для настройки параметров походки.

### 3.9.3 Интеграция с Nav2 и пример расчёта

Для интеграции traversability с Nav2 разработан мост `elevation_to_costmap_node.py`, который подписывается на `/elevation_map` (GridMap) и публикует `nav2_msgs/OccupancyGrid` на `/elevation_costmap`:

$$
\mathrm{cost} = 255 \times (1 - \mathrm{traversability})
$$

где cost = 0 (свободно) соответствует traversability = 1,0, cost = 254 (занято) — traversability ≈ 0,004, cost = 255 (неизвестно) — traversability = 0,0.

**Известная проблема: несоответствие QoS.** При подписке на `/elevation_map` с RELIABLE + VOLATILE map не доставляется, если publisher использует RELIABLE + TRANSIENT_LOCAL. Решение: явно указать TRANSIENT_LOCAL для subscriber.

**Известная проблема: сдвиг costmap.** Мост публикует costmap в frame_id = "odom", Nav2 ожидает в frame_id = "map". Статический publisher map → odom с нулевым смещением не обновляется при движении. Решение: удалить static_transform_publisher.

Nav2 настроен через `nav2_params.yaml` с `map_topic: /elevation_costmap`. Планировщик (SmacPlanner 2D) использует cost для выбора пути:

$$
\mathrm{edgeCost} = \mathrm{distance} \times \alpha + (1 - \mathrm{traversability}) \times \beta
$$

где $\alpha = 1,0$, $\beta = 5,0$. Пример: прямой путь через холм (10 м, traversability 0,3) — стоимость 13,5; обход (15 м, traversability 0,9) — стоимость 15,5. Хотя прямой путь короче, при увеличении $\beta$ до 10 обход становится дешевле (15,0 < 17,0).

### 3.9.4 Настройка весов

Веса w_slope, w_roughness, w_elevation являются настраиваемыми параметрами, которые могут быть адаптированы под конкретного робота и сценарий. Для лёгкого робота (малая инерция, высокий центр масс) следует увеличить w_slope для приоритета стабильности. Для шагающего робота с высоким подъёмом ног можно уменьшить w_elevation, так как робот способен преодолевать ступени. Для движения по склону вдоль горизонталей может быть добавлена асимметрия — различный вес для положительного и отрицательного gradient [12].

# Глава 2. Математические модели и методы

## 2.6 Математическая модель функции стоимости пути

Функция стоимости пути с учётом рельефа является ключевым отличием разработанного подхода от классических методов планирования. Вместо бинарной классификации проходимости (проходимо/непроходимо) вводится непрерывная оценка traversability, отражающая степень опасности каждой ячейки карты.

### 2.6.1 Понятие traversability

Traversability (проходимость) — количественная мера от $0{,}0$ (непроходимо) до $1{,}0$ (полностью проходимо). Вычисляется как взвешенная комбинация трёх факторов:

$$
\mathrm{traversability} = 1 - \bigl(w_{\mathrm{slope}} \cdot \mathrm{slopeCost} + w_{\mathrm{roughness}} \cdot \mathrm{roughnessCost} + w_{\mathrm{elevation}} \cdot \mathrm{elevationDiffCost}\bigr)
$$

где веса по умолчанию: $w_{\mathrm{slope}} = 0{,}5$, $w_{\mathrm{roughness}} = 0{,}3$, $w_{\mathrm{elevation}} = 0{,}2$. Выбор весов обоснован тем, что уклон поверхности вносит наибольший вклад в риск опрокидывания шагающего робота.

### 2.6.2 Компоненты стоимости

**Slope cost** — стоимость уклона поверхности. Максимальный безопасный угол наклона $\theta_{\max} = 25^\circ = 0{,}436$ рад определяется конструкцией ног и положением центра масс Unitree Go2:

$$
\mathrm{slopeCost} = \min\left(\frac{\mathrm{slope}}{\theta_{\max}}, 1{,}0\right)
$$

**Roughness cost** — стоимость шероховатости. Максимально допустимая шероховатость $R_{\max} = 0{,}10$ м:

$$
\mathrm{roughnessCost} = \min\left(\frac{\mathrm{roughness}}{R_{\max}}, 1{,}0\right)
$$

**Elevation difference cost** — стоимость перепада высот относительно уровня робота $z_{\mathrm{robot}}$:

$$
\mathrm{elevationDiffCost} = \min\left(\frac{|z - z_{\mathrm{robot}}|}{\Delta z_{\max}}, 1{,}0\right), \quad \Delta z_{\max} = 0{,}30\ \mathrm{м}
$$

### 2.6.3 Классификация типов местности

На основе traversability выделяются три класса местности:

| Класс | Traversability | Тип местности |
|-------|---------------|---------------|
| Safe | $> 0{,}7$ | Дорога, ровная поверхность, бетон |
| Medium | $0{,}3{-}0{,}7$ | Трава, гравий, мелкие камни, грунт |
| Unsafe | $< 0{,}3$ | Крупные камни, крутой склон, вода, ямы |

### 2.6.4 Интеграция с планировщиком

Для интеграции traversability с планировщиком Nav2 traversability конвертируется в cost (0–255):

$$
\mathrm{cost} = 255 \times (1 - \mathrm{traversability})
$$

где $\mathrm{cost} = 0$ (свободно) соответствует $\mathrm{traversability} = 1{,}0$, $\mathrm{cost} = 254$ (занято) соответствует $\mathrm{traversability} \approx 0{,}004$, $\mathrm{cost} = 255$ (неизвестно) — $\mathrm{traversability} = 0{,}0$.

Планировщик SmacPlanner использует взвешенную стоимость ребра:

$$
\mathrm{edgeCost} = \mathrm{distance} \times \alpha + (1 - \mathrm{traversability}) \times \beta
$$

где $\alpha = 1{,}0$, $\beta = 5{,}0$. Параметр $\beta$ регулирует приоритет безопасности над длиной пути. При $\beta = 10$ обход опасного участка становится дешевле прямого пути через него.

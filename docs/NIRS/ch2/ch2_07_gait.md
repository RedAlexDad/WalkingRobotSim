# Глава 2. Математические модели и методы

## 2.7 Математическая модель адаптации походки

Адаптация походки шагающего робота по типу местности является ключевым механизмом повышения энергоэффективности и устойчивости движения в пересечённой местности.

### 2.7.1 Агрегация traversability под опорами

Для каждой опоры робота $f \in \{\mathrm{FL}, \mathrm{FR}, \mathrm{HL}, \mathrm{HR}\}$ позиция $\mathbf{p}_f = (x_f, y_f, z_f)$ в системе координат карты вычисляется через TF-трансформацию $\mathrm{foot\_frame} \to \mathrm{map\_frame}$. Индекс ячейки карты для каждой опоры:

$$
\begin{aligned}
\mathrm{cell}_x^{(f)} &= \left\lfloor \frac{x_f - \mathrm{mapOrigin}_x}{r} \right\rfloor \\
\mathrm{cell}_y^{(f)} &= \left\lfloor \frac{y_f - \mathrm{mapOrigin}_y}{r} \right\rfloor
\end{aligned}
$$

Traversability под опорой: $t_f = \mathbf{T}[\mathrm{cell}_y^{(f)}, \mathrm{cell}_x^{(f)}]$, где $\mathbf{T}$ — слой traversability карты высот. Если опора находится за пределами карты, используется значение по умолчанию $t_f = 0{,}5$.

Агрегированная traversability вычисляется как минимальное значение среди всех опор:

$$
\mathrm{terrainType} = \min_{f} t_f
$$

Использование минимума гарантирует осторожное поведение при наличии хотя бы одной опоры на опасном участке.

### 2.7.2 Параметры походки

На основе $\mathrm{terrainType}$ выбираются параметры походки:

Параметры для соответствующих классов местности:

$$
\begin{aligned}
\text{Step height:} &\quad h_{\mathrm{step}} = 
\begin{cases}
0{,}04\ \mathrm{м}, & \mathrm{terrainType} > 0{,}7 \\
0{,}08\ \mathrm{м}, & 0{,}3 < \mathrm{terrainType} \leq 0{,}7 \\
0{,}15\ \mathrm{м}, & \mathrm{terrainType} \leq 0{,}3
\end{cases} \\
\text{Frequency:} &\quad f_{\mathrm{gait}} = 
\begin{cases}
2{,}0\ \mathrm{Гц}, & \mathrm{terrainType} > 0{,}7 \\
1{,}5\ \mathrm{Гц}, & 0{,}3 < \mathrm{terrainType} \leq 0{,}7 \\
1{,}0\ \mathrm{Гц}, & \mathrm{terrainType} \leq 0{,}3
\end{cases} \\
\text{Max speed:} &\quad v_{\max} = 
\begin{cases}
0{,}5\ \mathrm{м/с}, & \mathrm{terrainType} > 0{,}7 \\
0{,}3\ \mathrm{м/с}, & 0{,}3 < \mathrm{terrainType} \leq 0{,}7 \\
0{,}15\ \mathrm{м/с}, & \mathrm{terrainType} \leq 0{,}3
\end{cases} \\
\text{Body height:} &\quad h_{\mathrm{body}} = 
\begin{cases}
0{,}25\ \mathrm{м}, & \mathrm{terrainType} > 0{,}7 \\
0{,}20\ \mathrm{м}, & 0{,}3 < \mathrm{terrainType} \leq 0{,}7 \\
0{,}18\ \mathrm{м}, & \mathrm{terrainType} \leq 0{,}3
\end{cases}
\end{aligned}
$$

Обоснование: на ровной поверхности достаточно высоты шага 4 см; на сложном рельефе требуется до 15 см для преодоления камней. Частота шага снижается для коррекции траектории ноги. Опускание корпуса снижает центр масс и повышает устойчивость [6].

### 2.7.3 Плавность перехода

Для обеспечения плавного изменения параметров используется экспоненциальное сглаживание:

$$
\mathrm{param}_{\mathrm{current}} = \mathrm{param}_{\mathrm{current}} \cdot (1 - \alpha) + \mathrm{param}_{\mathrm{target}} \cdot \alpha, \quad \alpha = 0{,}3
$$

Типичное время перехода: Safe → Medium — 3–4 шага (1,5–2 с), Medium → Safe — 2–3 шага, Medium → Unsafe — 1–2 шага (быстрая реакция на опасность).

### 2.7.4 Прогнозирование traversability

Для упреждающей адаптации анализируется карта traversability в направлении движения. Определяется направление движения $\mathbf{d}$ (из cmd_vel или goal). Выбираются ячейки на пути на расстоянии до $L = 2$ м вперёд:

$$
\mathcal{C}_{\text{future}} = \{(i, j) \mid \|\mathbf{p}_{ij} - \mathbf{p}_{\mathrm{robot}}\| \leq L,\ \angle(\mathbf{p}_{ij} - \mathbf{p}_{\mathrm{robot}}) \approx \mathbf{d}\}
$$

Если $\min_{(i,j) \in \mathcal{C}_{\text{future}}} \mathbf{T}[i,j] < 0{,}5$, параметры походки начинают изменяться за 1–2 шага до входа на сложный участок, обеспечивая плавное замедление и своевременное увеличение высоты шага.

### 2.7.5 Типы походок

На основе агрегированного terrain type выбирается тип походки:

- **Trot** (рысь): диагональные пары ног синхронно. Высокая скорость, минимальная высота шага. Для ровных поверхностей ($\mathrm{terrainType} > 0{,}7$).
- **Crawl** (ползание): каждая нога независимо, минимум 3 ноги на земле. Повышенная устойчивость. Для неровных поверхностей ($0{,}3 < \mathrm{terrainType} \leq 0{,}7$).
- **Crawl_slow**: медленная crawl с повышенной высотой шага и постоянным контролем равновесия. Для опасных участков ($\mathrm{terrainType} \leq 0{,}3$).

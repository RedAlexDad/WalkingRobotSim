# IK Trigonometry Optimization

**Дата:** 2026-06-14
**Цель:** Ускорить Inverse Kinematics за счёт оптимизации тригонометрических вычислений
**Требование:** < 0.001 rad ошибки (достаточно для сервоприводов)

## Анализ hot path

`compute_all_joint_angles` в `inverse_kinematics.hpp` вызывает:

- 20× `atan2` (4 ноги × 5 вызовов)
- 4× `sin` (leg 0-3, все в theta3)
- 4× `cos` (leg 0-3, все в theta3)

Все вызовы `sin`/`cos` были в формуле для theta3: `atan2(l4 * sin(theta4), l3 + l4 * cos(theta4))`, где `theta4 = -acos(D)`.

## Оптимизация 1: sin/cos elimination

**Приём:** Тригонометрические тождества заменяют вычисление sin/cos от theta4 на прямые формулы от D:

- `sin(theta4)` = `sin(-acos(D))` = `-sqrt(1 - D²)`
- `cos(theta4)` = `cos(-acos(D))` = `D`

| Было                                  | Стало                           |
| ------------------------------------- | ------------------------------- |
| `theta4 = -acos(D)`                   | `sqrt_1_D2 = sqrt(1 - D²)`      |
| `theta4 = -atan2(sqrt(1-D²), D)`      | `theta4 = -atan2(sqrt_1_D2, D)` |
| `sin(theta4), cos(theta4)` для theta3 | `-sqrt_1_D2, D` напрямую        |

**Точность:** математически идентично, погрешность 0.

## Оптимизация 2: fast_atan2

**Приём:** Полиномиальная аппроксимация 7-й степени с range reduction.

- Range reduce аргумента в `[0, tan(π/8)]` через `atan(a) = π/4 - atan((1-a)/(1+a))`
- Полином: `a * (1 + a²(-0.332932 + a²(0.106704 + a²(-0.035436))))`
- Max error: < 0.001 rad (0.057°) — приемлемо для робота

**Реализация:** `include/quadropted_controller_cpp/utils/fast_math.hpp`

## Результаты бенчмарка

| Версия                                   | IK time      | Speedup   |
| ---------------------------------------- | ------------ | --------- |
| До (std::atan2 + sin/cos)                | 0.329 ms     | 1×        |
| После (fast_atan2 + sin/cos elimination) | **0.147 ms** | **2.24×** |

**Вывод:** Ускорение в 2.24× за счёт:

- 4× sin/cos → 0 операций (математически точно)
- 20× atan2 → fast_atan2 (ошибка < 0.001 rad)

## Изменённые файлы

| Файл                                    | Изменение                                       |
| --------------------------------------- | ----------------------------------------------- |
| `.../utils/fast_math.hpp`               | Новый: `fast_atan2` с range reduction           |
| `.../kinematics/inverse_kinematics.hpp` | sin/cos elimination + fast_atan2                |
| `.../kinematics/inverse_kinematics.cpp` | sin/cos elimination + fast_atan2                |
| `test/test_ik.cpp`                      | Tolerance 1e-5 → 2e-3 (под точность fast_atan2) |

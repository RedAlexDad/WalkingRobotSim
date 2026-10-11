# Webots как среда для сравнения RL и TROT-кинематики (Go2)

**Дата:** 2026-10-09
**Назначение:** оценить Webots как целевую среду для сравнения
RL-политики и модельного TROT/IK-контроллера четвероногого Unitree Go2.

---

## 1. Кратко

**Webots — рабочий вариант**, и в одном смысле удобнее Gazebo: для Go2 уже
есть готовый **модельный TROT + обратная кинематика** в ROS 2, то есть
готовый baseline для сравнения. Ограничение то же, что и у Gazebo:
**физика на CPU** (движок ODE), видеокарта физику не ускоряет.

## 2. Факты по Webots

| Аспект | Значение |
|---|---|
| Физический движок | **ODE** (Open Dynamics Engine) |
| Ускорение физики на GPU | нет (CPU) |
| Ускорение рендеринга на GPU | да (OpenGL) |
| Интеграция с ROS 2 | есть (`webots_ros2`) |
| Рельефы | elevation grid, неровные поверхности, ступени |
| Лицензия | Apache-2.0, свободная |
| Ориентир по ОС | Ubuntu 22.04 / ROS 2 Humble |

## 3. Готовые проекты (Go2 в Webots)

| Проект | Что даёт |
|---|---|
| `TuanLinh05/ROS2_Webots_DOG` | Go2 в Webots + ROS 2: походки trot/walk/pronk, двухзвенная **обратная кинематика**, контроллер (SMC), CSV-логи — **готовый baseline TROT/IK** |
| `tuzhongyi1983/go2w-webots` | Go2-W в Webots R2025a + ROS 2 Humble: управление, одометрия, два лидара |
| `EslaM-X/robopay-go2-tier1` | Навыки Go2, sim-to-sim MuJoCo + PyBullet + **Webots** harness |

## 4. Можно ли сравнить RL и TROT-кинематику

**Да.** Схема:

- **Baseline (model-based):** готовый trot + IK из `ROS2_Webots_DOG`.
- **RL:** политика, обученная (предпочтительно) **внутри Webots**.
- **Метрики:** скорость, высота корпуса и её разброс, крен/тангаж, дрейф,
  удельные затраты, падения — как в статье.
- **Сценарии:** плоскость → уклоны → неровности → ступени.

## 5. Главная оговорка

Если RL-политику обучать **не в Webots** (в PhysX/Isaac), а запускать в
Webots — это **sim-to-sim** (PhysX → ODE). По нашему опыту «в лоб» это не
работает. Для корректного сравнения RL нужно **обучать в Webots** (либо
переносить с domain randomization).

## 6. Webots против Gazebo (для нашей задачи)

| Критерий | Webots | Gazebo (gz-sim) |
|---|---|---|
| Физика на GPU | нет (ODE) | нет (DART) |
| Готовый Go2 + trot/IK | **да** | делали сами |
| Рельефы | удобные | есть, грубее |
| Наш готовый стек | нужно переносить | уже есть |
| Sim-to-sim для Isaac-политики | да | да |

## 7. План работ (черновик)

1. Поднять `ROS2_Webots_DOG` — получить baseline TROT/IK в Webots + ROS 2.
2. Убедиться, что baseline устойчиво ходит (плоскость).
3. Добавить RL-политику: обучение в Webots (или перенос с рандомизацией).
4. Свести метрики и сценарии (плоскость → уклоны → неровности).
5. Сравнить RL и TROT/IK, оформить результат.

## 8. Ссылки

- Webots (документация): https://cyberbotics.com/doc/reference/physics
- `ROS2_Webots_DOG`: https://github.com/TuanLinh05/ROS2_Webots_DOG
- `go2w-webots`: https://github.com/tuzhongyi1983/go2w-webots
- `robopay-go2-tier1`: https://github.com/EslaM-X/robopay-go2-tier1

---

## 9. Есть ли готовая RL-политика для Go2 в Webots?

**Нет.** Поиск не нашёл готовой обученной политики ходьбы Go2 для Webots.

Что есть по RL в Webots (но не «готовая политика Go2»):

| Проект | Что это |
|---|---|
| `aidudezzz/deepbots` | фреймворк RL для Webots (Python 3), обёртка «Webots ↔ gym-подобный env» |
| `aidudezzz/deepworlds` | примеры на deepbots (cartpole и др.) |
| `aniruddhkb/quadruped-webots-rl` | **свой** 8-DOF четвероног в Webots + «краткое RL для ходьбы» (не Go2) |
| `DragonKorn1/dqn_ppo_avoid_webots`, `*-cartpole` | учебные примеры RL в Webots (обход, cartpole) |

Готовые **Go2**-политики существуют для других сред:

| Среда | Готовая политика Go2 |
|---|---|
| Gazebo Classic | **да** (`rl_sar`) |
| Isaac Sim / Isaac Gym | да |
| MuJoCo | да |
| **Webots** | **нет** |

**Вывод:** в Webots RL-политику придётся **обучать самому** (через
`deepbots` или собственный harness) либо **переносить** (sim-to-sim).
Готового «взял и запустил» для Go2 в Webots нет.

# GPU и симуляция: можно ли ускорить Gazebo и где обучать на GPU

**Дата:** 2026-10-09
**Вопрос:** можно ли «переделать под GPU» обучение походки в Gazebo?

---

## 1. Короткий ответ

**Gazebo (gz-sim) по физике ускорить видеокартой нельзя.** Физика
считается на **CPU** (движки DART / Bullet / TPE в составе `gz-physics`).
GPU в Gazebo ускоряет только **рендеринг и сенсоры**, но не физику.

Чтобы обучать **на GPU**, нужно перейти на **GPU-движок физики** — а это
уже другой симулятор (и снова sim-to-sim при переносе в Gazebo).

## 2. Почему Gazebo — CPU

`gz-physics` — это абстрактный интерфейс над классическими CPU-движками.
GPU-плагина физики в gz-sim нет. Отсюда: темп симуляции определяется
процессором и сложностью сцены (что мы и наблюдали: RTF зависит от
нагрузки, а не от GPU).

## 3. Где реально есть GPU-физика (для обучения RL)

| Платформа | Что это | GPU-физика | Ссылка |
|---|---|---|---|
| **Isaac Lab / Isaac Sim** | RL-платформа NVIDIA | да (PhysX GPU) | isaac-sim.github.io/IsaacLab |
| **MuJoCo Warp (MJWarp)** | GPU-версия MuJoCo (DeepMind + NVIDIA) | да | github.com/google-deepmind/mujoco_warp |
| **Newton** | GPU-движок (на Warp + MJWarp) | да | github.com/newton-physics/newton |
| **Genesis World** | GPU мультифизика | да | github.com/Genesis-Embodied-AI/genesis-world |

Все они позволяют обучать тысячи параллельных сред на GPU — это и есть
«обучение на GPU».

## 4. Следствие (важное)

Обучение на GPU возможно **только в GPU-симуляторе**, который **не
Gazebo**. Значит:

- либо обучаем в GPU-симуляторе и **переносим** результат в Gazebo
  (sim-to-sim — ровно то, что у нас не сработало «в лоб»);
- либо обучаем **в самом Gazebo**, но тогда физика на CPU (медленно).

Смягчить sim-to-sim помогает **domain randomization** (рандомизация
трения, масс, задержек, задержек привода, шума датчиков) — политика
становится устойчивее к различиям движков.

## 5. Что это значит для нас

| Вариант | GPU | Перенос | Комментарий |
|---|---|---|---|
| Обучать в Isaac Lab + рандомизация | да | sim-to-sim | шанс на перенос |
| Обучать в MuJoCo Warp / Newton | да | sim-to-sim | современный GPU-путь |
| Обучать в Gazebo | нет | нет gap | медленно, CPU |

## 6. Рекомендация

1. Если цель — **быстро обучить и получить походку в Gazebo**: обучать в
   **GPU-симуляторе с domain randomization**, затем верифицировать в
   Gazebo (минимальная сцена, RTF≈1.0).
2. Если цель — **гарантированный перенос**: обучать **в Gazebo** (пусть
   медленно) — тогда среда обучения = среда исполнения.
3. GPU в нашем контейнере включается пробросом NVIDIA
   (`nvidia-container-toolkit` есть на хосте); для GPU-симулятора нужен
   отдельный образ/окружение (Isaac Lab, MJWarp, Newton, Genesis).

## 7. Ссылки

- Gazebo physics engines (CPU): https://github.com/gazebosim/gz-physics
- MuJoCo Warp (GPU): https://github.com/google-deepmind/mujoco_warp
- Newton (GPU): https://github.com/newton-physics/newton
- Genesis World (GPU): https://github.com/Genesis-Embodied-AI/genesis-world
- Isaac Lab (GPU): https://isaac-sim.github.io/IsaacLab

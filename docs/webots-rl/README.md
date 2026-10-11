# webots-rl — сравнение RL и TROT/IK для Go2 в Webots

Рабочая папка по оценке **Webots** как среды для сравнения RL-политики и
модельного TROT/IK-контроллера четвероногого Unitree Go2.

| Файл | Что это |
|---|---|
| `plan.md` | факты по Webots, готовые Go2-проекты, сравнение с Gazebo, план |

Ключевое:

- Webots — физика **ODE на CPU** (GPU физику не ускоряет, как и в Gazebo);
- для Go2 уже есть **готовый TROT/IK** в Webots + ROS 2 (baseline);
- сравнение с RL реализуемо, но RL лучше **обучать в Webots** — иначе
  снова sim-to-sim.

Связанные материалы: `docs/gazebo-rl-vs-ik/`,
`reports/gazebo-rl/2026-10-09_gazebo-rl-sim2sim.md`.

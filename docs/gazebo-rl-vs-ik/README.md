# gazebo-rl-vs-ik — сравнение RL и IK/TROT в Gazebo

Рабочая папка по сравнению обученной RL-политики и модельного
IK/TROT-контроллера **в Gazebo** (gz-sim). MuJoCo и Isaac Sim как среда
не рассматриваются.

| Файл | Что это |
|---|---|
| `plan.md` | полный план: стек, топики, вектор наблюдений, риски, этапы |
| `run-log.md` | журнал прогонов и наблюдений (заполняется по ходу) |

Прототип узла: `src/gazebo_sim/scripts/go2_policy_gz.py`.

Связанные материалы:

- `docs/ieee-article/` — статья, метрики, телеметрия, рисунки (PIERE/REEPE).
- `src/mujoco/go2_policy_mj.py` — рецепт наблюдений/действий (только как
  спецификация).
- `src/gazebo_sim/launch/launch.launch.py` — запуск Gazebo с контроллером.

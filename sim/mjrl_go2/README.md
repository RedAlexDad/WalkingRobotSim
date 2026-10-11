# sim/mjrl_go2 — Go2 в MuJoCo Playground (GPU)

Форк окружения Go1 из MuJoCo Playground под робота **Unitree Go2**, чтобы
обучать RL-политику походки на GPU и затем переносить её в наш gz-sim
(Gazebo Harmonic).

## Зачем

Предобученная PhysX-политика в наш gz-sim не переносится (нулевой
перенос). Стратегия — обучить политику с domain randomization в
GPU-симуляторе и перенести (см. `docs/gpu-rl-training/`).

В Playground есть Go1, но нет Go2. Здесь Go1-задача переиспользована
без изменений, а константы и загрузчик ассетов пропатчены под MJCF Go2
из MuJoCo Menagerie.

## Файлы

| Файл | Назначение |
|---|---|
| `go2_env.py` | форк: патчит константы/ассеты Go1-задачи под Go2 |
| `go2_trot_env.py` | вариант с наградой за отслеживание рыси (bootstrap) |
| `train_go2.py` | обучение PPO (brax), CSV-лог в `results/` |
| `eval_go2.py` | оценка политики, CSV-траектория в `results/` |
| `train_native.py` | контроль: обучение нативного окружения Playground |
| `render_go2.py` | рендер поведения политики в PNG (EGL) |
| `xmls/go2_robot.xml` | MJCF Go2 с `position`-актуаторами (как Go1) |
| `xmls/scene_go2_flat.xml` | сцена: пол + сенсоры под контракт Go1-задачи |
| `results/` | CSV обучения (`*_train.csv`) и оценок (`*_eval.csv`) |

## Ключевые адаптации

- `ROOT_BODY` = `base`; сайты стоп `*_foot`; гемы стоп `FR/FL/RR/RL`.
- Добавлены сенсоры `upvector`, `local_linvel`, `*_pos`, `*_global_linvel`
  и контакты `*_floor_found`.
- Актуаторы переведены в `position` (как у Go1), физика контакта — как у
  Go1 (коллизии только стоп с полом).

## Окружение

`.venv-mjrl` (Python 3.12): mujoco 3.15, jax 0.10.2 (GPU, `sm_120`),
mujoco-warp, mujoco_playground, brax.

## Статус

Окружение обучается на GPU. К текущему моменту политика стабилизируется
(стоит/марширует), но **устойчивого поступательного движения пока нет**;
ведутся эксперименты по награде/инициализации.

# CHAMP-эталон для доводки TrotGait (метод C)

**Дата:** 2026-09-27
**Источник:** `github.com/darshmenon/quadruped-robotics-stack` →
`config/go2_champ/gait.yaml` (CHAMP, кинематический gait engine).

## Параметры CHAMP для Unitree Go2

| Параметр | Значение CHAMP Go2 |
|---|---|
| `knee_orientation` | `">>"` |
| `pantograph_leg` | false |
| `odom_scaler` | 0.9 |
| `max_linear_velocity_x` | 0.5 м/с |
| `max_linear_velocity_y` | 0.25 м/с |
| `max_angular_velocity_z` | 1.0 рад/с |
| `com_x_translation` | 0.0 |
| `swing_height` | **0.04 м** |
| `stance_depth` | 0.00 |
| `stance_duration` | **0.25 с** |
| `nominal_height` | **0.32 м** |

## Сравнение с нашим TrotGait

| Параметр | CHAMP Go2 | Наш TrotGait | Комментарий |
|---|---|---|---|
| Высота подъёма лапы | **0.04 м** | 0.14 м (было) | у нас в 3.5× выше |
| Длительность стойки | **0.25 с** | `stance_time=0.04` | у нас в 6× короче |
| Высота корпуса | **0.32 м** | 0.25 м | у нас ниже |
| Макс. скорость | 0.5 м/с | — | — |

## Что применено

- `z_leg_lift`: 0.14 → **0.04** (`trot/gait.rs`, по CHAMP Go2).

## Статус

Правка применена, но в MuJoCo робот **стоит** (roll=0, x=−0.034). Диагностика
показала, что **мост не получает команды контроллера** (поток
`/robot1/joint_group_controller/commands` не доходит host←container — QoS/DDS).
Поэтому текущий результат «стоит» отражает не контроллер, а **обрыв канала
команд**; до его устранения сравнение некорректно.

## Следующий шаг

1. Починить QoS/DDS между контейнером (Jazzy) и мостом (host, Lyrical):
   вероятно, несовместимость RELIABLE/BEST_EFFORT или разные профили CycloneDDS.
2. После этого — повторить прогон и сравнить с эталонными значениями CHAMP.

## Примечание

CHAMP в этом репозитории **не привязан к физике Go2** (использует generic
reference robot), поэтому его `gait.yaml` — ориентир по параметрам, а не
готовый запускаемый стенд для Go2.

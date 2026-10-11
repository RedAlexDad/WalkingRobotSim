# rl_sar — запуск RL-походки Go2 в Gazebo (результат)

**Дата:** 2026-10-09
**Ветка:** `feat/rl-sar`
**Цель:** собрать окружение **fan-ziqi/rl_sar** и проверить RL-походку
Unitree Go2 в Gazebo.

---

## 1. Итог (главное)

**Получилось.** После сборки окружения rl_sar робот Go2 в Gazebo:
1. **встал** (лог: `Getting up completed`),
2. вошёл в режим походки (`RL Controller`),
3. **пошёл вперёд** — прошёл ≈ **3.4–3.5 м** (мир `stairs`, с подъёмом по
   лестнице), стойка ≈ 0.28 м.

Это подтверждает: **рабочая RL-походка в Gazebo достижима готовым стеком**
rl_sar (его политика обучена под его же среду).

## 2. Что такое rl_sar

Фреймворк «sim & real»: запуск RL-политик роботов в симуляторе и на
железе. Для Go2 — политики `himloco` / `robot_lab`, среда **Gazebo
Classic** + ROS 2 Humble, свой контроллер суставов (позиция + kp/kd +
момент), control-loop 200 Гц, политика 50 Гц.

## 3. Проблемы при сборке и их решения

| Проблема | Причина | Решение |
|---|---|---|
| `Cannot download robot descriptions in offline mode` | `is_online` в `build.sh` делает `curl --head github.com` — в сборке вернул ошибку | предзагрузка описаний на хосте (сеть есть) |
| Тяжёлая загрузка libtorch (таймаут) | большой файл + возможный срыв | загрузка с докачкой на хосте |
| `add_subdirectory` без `CMakeLists.txt` | не инициализированы сабмодули | `git submodule update --init --recursive` |
| FastDDS SHM `open_and_lock_file failed` | малый `/dev/shm` (64 МБ) + `ipc: host` у двух контейнеров | профиль **UDP-only** + остановка второго контейнера |
| `gzclient` падает (`Authorization required`) | нет X-авторизации | headless `gzserver` достаточно |
| `rl_sim` падает: `Controller already loaded` | контроллер `robot_joint_controller` поднимает сам `rl_sim`, при повторном запуске уже загружен | свежий перезапуск лаунча, **один** прогон `rl_sim` |
| Ввод с клавиатуры не работает | нужен TTY | управление через **gamepad `/joy`** |

## 4. Порядок запуска (кратко)

1. Предзагрузить на хосте: описания роботов (`src/rl_sar_zoo`) и
   inference-рантайм (libtorch, onnxruntime).
2. Инициализировать сабмодули.
3. Создать профиль FastDDS UDP-only и экспортировать его как переменную
   окружения.
4. Собрать образ (`docker compose build`) и поднять контейнер
   (`docker compose up -d`).
5. Запустить Gazebo: `ros2 launch rl_sar gazebo.launch.py rname:=go2`.
6. Запустить политику: `ros2 run rl_sar rl_sim rname:=go2`.
7. Управлять через топик `/joy`.

## 5. Управление через `/joy` (gamepad)

| Действие | Сообщение |
|---|---|
| Встать (GetUp) | button[0] = 1 |
| Походка (RLLocomotion) | button[5] = 1 и axes[7] > 0 |
| Вперёд | axes[1] (LY) |
| Вбок | axes[0] (LX) |
| Поворот | axes[3] (RX) |
| Сброс | button[5] = 1 и button[3] = 1 |

## 6. Результаты (наблюдения)

- `RL Controller [himloco] x:0.30` — команда принята;
- поза робота по Gazebo: x: 0.13 → 1.12 → 1.75 → 2.33 → 2.56 → **3.41**;
  (мир `stairs`, z растёт — подъём по лестнице);
- робот устойчиво стоит и идёт; падений на малой команде не зафиксировано.

## 7. Вывод и связь с нашим проектом

- **RL-походка Go2 в Gazebo работает** — но через стек rl_sar (Gazebo
  Classic, их политика).
- Наша попытка запустить **чужую (NVIDIA PhysX) политику** в нашем gz-sim
  дала sim-to-sim провал (см. `reports/gazebo-rl/2026-10-09_gazebo-rl-sim2sim.md`).
  rl_sar же использует **свою** политику под **свою** среду — потому и идёт.

## 8. Сравнение с нашим gz-sim

| Аспект | rl_sar | наш порт |
|---|---|---|
| Симулятор | Gazebo Classic | gz-sim (Harmonic) |
| ПО | ROS 2 Humble | ROS 2 Jazzy |
| Политика | своя (himloco/robot_lab) | чужой NVIDIA PhysX |
| Результат | **идёт** | оседает (sim-to-sim) |

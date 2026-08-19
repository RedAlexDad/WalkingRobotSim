# Report 2026-06-05 10:27:29 MSK

**Branch:** fix/dockerfile
**Stats:**  1 file changed, 24 insertions(+), 1 deletion(-)

## What was added
- `rosdep install --skip-keys "Eigen3 torch ultralytics"` — rosdep разрешает зависимости из package.xml, пропуская pip/system-пакеты

## What was changed
- `src/docker/Dockerfile` — добавлен `--skip-keys` для Eigen3, torch, ultralytics; добавлен `libeigen3-dev` в base-system

## Problems encountered
- `rosdep install` упал с ошибкой: `Cannot locate rosdep definition for [Eigen3]` — Eigen3 не является ROS-пакетом, это системная библиотека (libeigen3-dev)
- Та же ошибка для `torch` и `ultralytics` — это pip-пакеты, не известные rosdep

## How they were solved
- Добавлен флаг `--skip-keys "Eigen3 torch ultralytics"` — rosdep пропускает эти ключи, не пытаясь найти apt-пакет
- `libeigen3-dev` установлен в base-system (apt), torch и ultralytics — в python-deps (pip)

## Notes for the future
- При добавлении нового pip-пакета в `package.xml` — добавить его в `--skip-keys`
- Если rosdep найдёт apt-аналог пакета в будущем — `--skip-keys` можно убрать

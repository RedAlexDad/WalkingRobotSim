# Когда пересобирать пакет, а когда достаточно перезапустить симуляцию

## Как устроена установка (install)

В контейнере `walking_robot_sim` пакет `gazebo_sim` установлен через `colcon build`
с типом `symlink-install`. Это означает, что **почти все файлы в `install/` —
симлинки (symlink)** на исходники в `src/`.

Проверить можно так:

```bash
docker exec walking_robot_sim bash -c '
find /root/ws/install/gazebo_sim -type f -o -type l | while read f; do
    if [ -L "$f" ]; then
        echo "SYMLINK $f"
    else
        echo "COPY    $f"
    fi
done
'
```

Результат: всё, кроме `package.sh`, `package.ps1`, `package.dsv`, `hook/*.dsv`,
`hook/*.ps1`, `hook/*.sh` и cmake-файлов — симлинки. В частности:

- **Python-скрипты** (`*.py`) — симлинки
- **Launch-файлы** (`*.launch.py`) — симлинки
- **Конфиги** (`*.yaml`, `*.rviz`) — симлинки
- **Модели/карты** (`.sdf`, `.pgm`, `.dae`) — симлинки
- **CMakeLists.txt, package.xml** — НЕ симлинки (используются только при сборке)

## Что это значит на практике

### Пересборка НЕ нужна — достаточно перезапустить процесс

Если меняете:

| Файл | Тип | Действие |
|------|-----|----------|
| `scripts/waypoint_collector.py` | Python script | Перезапустить ноду (или всю симуляцию) |
| `launch/*.launch.py` | launch-файл | Перезапустить launch |
| `config/*.yaml` | конфиг | Перезапустить ноду, которая его читает |
| `rviz/*.rviz` | конфиг RViz | Перезагрузить RViz |
| `models/*` | модели | Перезапустить Gazebo |
| `maps/*` | карты | Перезапустить Nav2 |

Потому что ROS 2 читает эти файлы из `install/`, а `install/` — это просто ссылка
на `src/`. Изменения в `src/` видны мгновенно.

Пример:

```bash
# Поправили waypoint_collector.py в src/
# Достаточно просто перезапустить ноду:
docker exec walking_robot_sim bash -c 'source /opt/ros/jazzy/setup.bash && ros2 service call /clear_waypoints std_srvs/Trigger'
# Или перезапустить всю симуляцию через make gazebo-cpp
```

### Пересборка НУЖНА

Если меняете:

| Файл | Почему |
|------|--------|
| `CMakeLists.txt` | Меняет мета-информацию пакета |
| `package.xml` | Меняет зависимости |
| Добавляете **новый** Python-скрипт в `scripts/` | `colcon build` должен создать новый symlink в `install/` |
| C++ исходники (`.cpp` в других пакетах) | Требуют компиляции |
| Добавляете/удаляете launch-файл или конфиг из `CMakeLists.txt` | `install` не узнает о новом файле без пересборки |

Пример, когда пересборка нужна:

```bash
# Добавили новый файл src/gazebo_sim/scripts/new_script.py
# и добавили его в CMakeLists.txt
colcon build --packages-select gazebo_sim
```

### Итог

**Правило:** если файл уже существовал и вы его просто редактируете —
`colcon build` не нужен, достаточно перезапустить процесс.
Пересборка нужна только когда меняется структура пакета (новые файлы,
зависимости, C++ код).

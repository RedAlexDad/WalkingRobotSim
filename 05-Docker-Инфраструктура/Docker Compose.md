# Docker Compose

## Файл
`src/docker/compose.yml`

## Описание

Docker Compose конфигурация для запуска симулятора с X11 GUI passthrough, host networking и ограничениями ресурсов.

## Сервис: `simulator`

### Образ
- **Image:** `walking_robot_sim:latest`
- **Container:** `walking_robot_sim`
- **Build context:** `../` (корень проекта)
- **Dockerfile:** `docker/Dockerfile`
- **Target:** `final`

### Сеть и доступ
| Параметр | Значение | Описание |
|---|---|---|
| `network_mode` | `host` | Сетевой стек хоста |
| `ipc` | `host` | Общий IPC с хостом |
| `privileged` | `true` | Расширенные привилегии |
| `tty` | `true` | Псевдо-TTY |
| `stdin_open` | `true` | Интерактивный stdin |

### GUI Passthrough (X11)

**Volumes:**
- `/tmp/.X11-unix:/tmp/.X11-unix:rw` — сокет X11
- `${XAUTHORITY}:/tmp/.Xauthority:rw` — авторизация X

**Environment:**
- `DISPLAY: ${DISPLAY}`
- `XAUTHORITY: /tmp/.Xauthority`
- `QT_X11_NO_MITSHM: "1"` — отключить MIT-SHM

### Переменные окружения ROS

| ENV | Значение |
|---|---|
| `RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp` |
| `ROS_DOMAIN_ID` | `0` |
| `ROS_DISTRO` | `jazzy` |
| `CYCLONEDDS_URI` | `file:///cyclonedds.xml` |
| `GAZEBO_RESOURCE_PATH` | `/usr/share/gazebo-11` |
| `GZ_SIM_RESOURCE_PATH` | `/root/ws/src/gazebo_sim/models/` |
| `WORKSPACE_DIR` | `/root/ws` |
| `ROS_LOG_DIR` | `/root/ws/logs` |

### Volumes

| Host | Container | Описание |
|---|---|---|
| `./cyclonedds.xml` | `/cyclonedds.xml:ro` | DDS конфиг |
| `./logs/gazebo` | `/root/ws/logs` | Логи Gazebo |
| `./data/gazebo` | `/root/ws/data` | Данные Gazebo |
| `project_src` | `/root/ws/src/` | Исходный код |

### Ограничения ресурсов

| Ресурс | Limit | Reservation |
|---|---|---|
| Memory | 24G (75%) | 8G (25%) |
| CPUs | 12.0 (75%) | 4.0 (25%) |

### Cache from

Все 10 этапов сборки указаны в `cache_from` для ускорения повторных сборок:
- `base-system`, `ros-core`, `ros-control`, `ros-simulation`, `ros-navigation`, `ros-vision`, `ros-tools`, `python-deps`, `workspace`, `latest`

### Command

```yaml
command: bash -c "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash && tail -f /dev/null"
```

Контейнер запускается в фоновом режиме с sourced ROS workspace.

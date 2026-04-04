# CI/CD — GitHub Actions

## Файлы

- `.github/workflows/ci.yml` — базовая CI (build + smoke test)
- `.github/workflows/test.yml` — полное тестирование симуляции

## Триггеры

| Событие | Ветки |
|---|---|
| `push` | `main`, `jazzy` |
| `pull_request` | `main`, `jazzy` |
| `workflow_run` | После успешного CI (для test.yml) |

## Workflow: CI (`ci.yml`)

### Job: `docker-build`

| Шаг | Описание |
|---|---|
| Checkout | Клонирование репозитория |
| Docker Buildx | Настройка Buildx |
| Free disk space | Удаление dotnet, ghc, boost, prune Docker |
| Build Docker image | `docker build --no-cache -t walking_robot_sim:test .` |
| Test container | `docker compose up -d`, ожидание 30с, `ros2 node list` |
| Upload artifacts | `test_results.txt`, `container_logs.txt` (7 дней) |

## Workflow: Simulation Tests (`test.yml`)

### Job: `simulation-test`

| Шаг | Описание |
|---|---|
| Build | Сборка Docker образа |
| Start simulation | `docker compose up -d`, ожидание 45с |
| Launch Gazebo | `ros2 launch gazebo_sim launch.py`, timeout 60с |
| Wait for ready | Цикл до 90 попыток (2с) — поиск узлов gazebo/robot/controller |
| Check ROS nodes | `ros2 node list` → `ros_nodes.txt` |
| List all topics | `ros2 topic list` → `all_topics.txt` |
| Check robot topics | grep `/robot1/(joint_states\|cmd_vel\|odom\|scan\|robot_mode)` → `robot_topics.txt` |
| Test teleop | `ros2 topic pub /robot1/cmd_vel` + проверка odom |
| Check lidar | `ros2 topic echo /robot1/scan --once` |
| Test stability | Проверка joint_states, robot_mode, отправка команды движения, проверка отзывчивости ROS |
| Cleanup | `docker compose down`, `docker system prune` |
| Upload artifacts | `simulation_summary.txt`, `ros_nodes.txt`, `all_topics.txt`, `robot_topics.txt` |

## Артефакты

| Workflow | Артефакт | Файлы | Хранение |
|---|---|---|---|
| CI | `ci-results` | `test_results.txt`, `container_logs.txt` | 7 дней |
| Simulation | `simulation-results` | `simulation_summary.txt`, `ros_nodes.txt`, `all_topics.txt`, `robot_topics.txt` | 7 дней |

## Оптимизация дискового пространства

Оба workflow освобождают место перед сборкой:
```bash
sudo rm -rf /usr/share/dotnet /opt/ghc "/usr/local/share/boost"
sudo apt-get clean
docker system prune -a -f
```

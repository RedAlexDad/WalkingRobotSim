# Kubernetes vs Docker Compose — Анализ

## Вердикт

> **Docker Compose v2 — оптимальный выбор.** Kubernetes не нужен на текущем этапе проекта.

---

## Почему Kubernetes НЕ нужен

### 1. Масштаб проекта

| Параметр      | WalkingRobotSim       | Типичный K8s use-case   |
| ------------- | --------------------- | ----------------------- |
| Контейнеров   | 1 (simulator)         | 10-100+                 |
| Микросервисов | Монолитная симуляция  | Распределённая система  |
| Трафик        | Локальный (localhost) | Сетевой между сервисами |
| Реплик        | 1                     | 3-10+ для HA            |

Kubernetes — оверинжиниринг для 1 контейнера.

### 2. Накладные расходы

- **K8s минимальные:** ~1-2 GB RAM + CPU на инфраструктуру (etcd, kubelet, kube-proxy, CNI)
- **Проект использует:** 8-24 GB RAM, 4-12 CPU
- **Итог:** K8s съест 10-15% ресурсов впустую

### 3. Специфические требования проекта

| Требование | Docker Compose | Kubernetes |
|---|---|---|
| **GUI (X11 forwarding)** | ✅ Из коробки | ❌ Сложные костыли |
| **Host network** | ✅ `network_mode: host` | ❌ Ограничено |
| **Privileged mode** | ✅ `privileged: true` | ⚠️ Требует PSP/PSA |
| **Доступ к железу** | ✅ Простой | ❌ DevicePlugin |
| **Real-time (<1ms)** | ✅ Прямой доступ | ⚠️ Доп. латентность |

Проект критически зависит от:
- X11 для Gazebo GUI
- Host network для ROS 2 (CycloneDDS)
- Privileged для доступа к системным ресурсам
- Низкой задержки для контроллеров реального времени

### 4. Сложность разработки

**Docker Compose:**
```bash
docker compose up -d
docker compose exec simulator bash
docker compose logs -f
```

**Kubernetes:**
```bash
kubectl apply -f deployment.yaml
kubectl exec -it pod-name -- bash
kubectl logs -f pod-name
kubectl port-forward ...
# + настройка minikube/kind + host network config
```

Для локальной разработки Compose в 5-10 раз быстрее.

### 5. CI/CD

Текущие workflow используют Docker Compose напрямую. Переход на K8s потребует:
- Kind/Minikube в CI
- Манифесты (Deployment, Service, ConfigMap...)
- Helm chart (опционально)
- Усложнение pipeline на 30-50%

---

## Когда Kubernetes ИМЕЛ БЫ смысл

| Сценарий | Применимо сейчас? |
|---|---|
| Мульти-робот симуляция (10+ роботов одновременно) | ❌ Нет |
| Распределённая симуляция на несколько нод | ❌ Нет |
| Продакшен deployment с HA | ❌ Нет (исследовательский проект) |
| Автоскейлинг по нагрузке | ❌ Нет (фиксированная нагрузка) |
| Мульти-окружения (dev/stage/prod) | ❌ Нет (только dev) |
| GitOps с ArgoCD/Flux | ❌ Избыточно |

---

## Архитектура: текущая vs гипотетическая K8s

### Текущая (Docker Compose)
```
┌─────────────────────────────────────┐
│   Docker Compose (1 сервис)         │
│  ┌─────────────────────────────┐    │
│  │  walking_robot_sim          │    │
│  │  - ROS 2 Jazzy              │    │
│  │  - Gazebo Harmonic          │    │
│  │  - Python контроллеры       │    │
│  │  - CycloneDDS               │    │
│  │  - Nav2 + SLAM              │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### Гипотетическая (Kubernetes)
```
┌──────────────────────────────────────────────┐
│  Kubernetes Cluster                          │
│  ┌────────────────────────────────────────┐  │
│  │  Pod: walking-robot-sim                │  │
│  │  ┌──────────────────────────────────┐  │  │
│  │  │  Container: simulator            │  │  │
│  │  └──────────────────────────────────┘  │  │
│  └────────────────────────────────────────┘  │
│  + etcd + kubelet + kube-proxy + CNI + ...  │
└──────────────────────────────────────────────┘
```

**Добавленная сложность:** 5-6 дополнительных компонентов для 1 контейнера.

---

## Рекомендации по улучшению Docker Compose

### Высокий приоритет

#### 1. Профили для разных сценариев
```yaml
services:
  simulator:
    profiles: ["full", "gui"]
    # ... полная конфигурация с GUI

  simulator-headless:
    profiles: ["ci", "headless"]
    <<: *basic_nogui
    image: walking_robot_sim:latest
    command: ros2 launch gazebo_sim launch_python.launch.py
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '8.0'
```

#### 2. Logging driver с ротацией
```yaml
services:
  simulator:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
        compress: "true"
```

### Средний приоритет

#### 3. .env файл для переменных
```bash
# .env
ROS_DOMAIN_ID=0
DISPLAY=:0
WORKSPACE_DIR=/root/ws
COMPOSE_PROJECT_NAME=walking_robot_sim
```

#### 4. stop_grace_period для корректной остановки
```yaml
services:
  simulator:
    stop_grace_period: 30s
    stop_signal: SIGINT
```

#### 5. Улучшенный health check
```yaml
healthcheck:
  test:
    - "CMD"
    - "bash"
    - "-c"
    - |
      source /opt/ros/jazzy/setup.bash &&
      source /root/ws/install/setup.bash &&
      ros2 node list | grep -q controller
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 90s
```

### Низкий приоритет (будущее)

#### 6. Override файл для разработки
`compose.override.yml`:
```yaml
services:
  simulator:
    volumes:
      - ./../src/quadropted_controller:/root/ws/src/quadropted_controller:rw
      - ./../src/gazebo_sim:/root/ws/src/gazebo_sim:rw
    build:
      target: workspace
```

#### 7. Профили для разных роботов
```yaml
services:
  simulator-go2:
    profiles: ["go2"]
    environment:
      ROBOT_MODEL: go2

  simulator-go1:
    profiles: ["go1"]
    environment:
      ROBOT_MODEL: go1
```

---

## Альтернативы на будущее

Если понадобится оркестрация для нескольких роботов (по возрастанию сложности):

1. **Docker Compose с несколькими сервисами** — до 5-10 роботов
2. **Docker Swarm** — легковесная оркестрация
3. **K3s/K3d** — легковесный K8s для edge
4. **Полный Kubernetes** — только при реальной необходимости

---

## Итоговая оценка

| Критерий | Docker Compose | Kubernetes |
|---|---|---|
| Простота | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Производительность | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| GUI поддержка | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Разработка | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| CI/CD | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Масштабируемость | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| High Availability | ⭐ | ⭐⭐⭐⭐⭐ |

**Текущая архитектура на Docker Compose — правильный выбор. Не менять без реальной необходимости.**

# Docker Build Rules

## Layer Caching

- **ЗАПРЕЩЕНО** использовать `--no-cache` в production-сборках (`make deploy`, `make elevation-cpu`)
- `--no-cache` допустим только в целях: `make build-no-cache`, `make test-build`
- Docker layer cache работает автоматически при `docker compose build` без флагов

## Структура Dockerfile (для максимального кэширования)

Порядок слоёв имеет значение. От менее изменяемого к более изменяемому:

```
1. FROM base image              ← редко меняется
2. apt install system deps      ← редко меняется (только package.xml)
3. pip install Python deps      ← редко меняется (только requirements.txt)
4. COPY source code             ← меняется часто
5. colcon build                 ← меняется при изменении кода
```

## Dockerfile Syntax

- **НЕ ИСПОЛЬЗОВАТЬ** `# syntax=docker/dockerfile:1.4` — требует внешнего парсера из Docker Hub
- Docker Engine 24+ поддерживает Dockerfile 1.4 нативно
- Использовать стандартный синтаксис Dockerfile

## Умные сборки

Проект использует smart-скрипты для определения необходимости пересборки:

| Скрипт | Назначение | Вызов |
|--------|-----------|-------|
| `scripts/smart-deploy.bash` | Сборка основного образа | `make deploy` |
| `scripts/smart-elevation.bash` | Сборка elevation образа | `make elevation-build` |

Они проверяют git diff с последним собранным коммитом и пропускают сборку если изменений нет.

## Volume Mounts

Для разработки Python-кода без пересборки Docker используйте volume mounts:

```yaml
volumes:
  - ./src/walking_robot_utils/:/ws/install/.../site-packages/walking_robot_utils/:ro
```

## Переменные окружения для сборки

- `DOCKER_BUILDKIT=1` — включить BuildKit (ускорение сборки)
- `COMPOSE_DOCKER_CLI_BUILD=1` — использовать docker CLI для сборки

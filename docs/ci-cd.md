# CI/CD

Непрерывная интеграция через GitHub Actions. Два workflow: CI (быстрая проверка качества) и Simulation Test (полная интеграция).

---

## Workflow: CI

Триггеры: `push` в `main`/`jazzy`, `pull_request` в `main`/`jazzy`.

Шаги:

| Шаг | Описание |
|-----|----------|
| **Docker build** | Сборка образа (с кэшем между запусками) |
| **YAML lint** | yamllint всех `.yaml`/`.yml` файлов |
| **Python lint** | flake8 + pylint контроллеров и скриптов |
| **C++ lint** | clang-tidy C++ контроллера |
| **C++ unit tests** | gtest (27 тестов) |

Время выполнения: 5-10 минут.

---

## Workflow: Simulation Test

Триггеры: `push` в `main`/`jazzy`, `pull_request` в `main`/`jazzy`.

Интеграционные тесты внутри контейнера:

| Тест | Что проверяет |
|------|---------------|
| **Container up** | Контейнер стартует и работает |
| **ROS 2 topics** | Ожидаемые топики публикуются (joint_states, odom, tf) |
| **Gazebo ready** | Gazebo Sim загружен и публикует /clock |
| **Controller test** | Контроллер реагирует на команды |

---

## Локальные проверки

Те же проверки можно запустить локально:

```bash
# Линтинг всех языков
make ci-lint

# Линтинг отдельно
make ci-lint-yaml
make ci-lint-python
make ci-lint-cpp

# C++ unit тесты
make ci-test-cpp
```

---

## Конфигурация

- `.github/workflows/ci.yml` — CI workflow
- `.github/workflows/simulation-test.yml` — Simulation Test workflow
- `.yamllint` — конфиг yamllint
- `.clang-tidy` — конфиг clang-tidy
- `setup.cfg` — конфиг flake8 / pylint

---

## Разработка

Для добавления нового шага в CI:
1. Отредактировать `.github/workflows/ci.yml`
2. Убедиться, что шаг выполняется внутри собранного Docker контейнера
3. Проверить локально через `make ci-*`

Для добавления интеграционного теста:
1. Добавить скрипт в `src/tests/`
2. Добавить шаг в `.github/workflows/simulation-test.yml`

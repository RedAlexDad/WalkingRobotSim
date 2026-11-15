# CI/CD

Непрерывная интеграция через GitHub Actions: workflow `CI` — линтеры,
Rust-тесты, сборка Docker-образа и smoke-тесты в контейнере.

---

## Workflow: CI

Триггеры: `push` в `main`, `jazzy_cpp`, `feat/rust-*`; `pull_request`
в `main`; ручной `workflow_dispatch`.

| Job | Описание |
|-----|----------|
| **lint** | yamllint (`workflow-файлы`, `src/docker/*.yml`) + ruff для `src/` |
| **rust-tests** | `cargo test --workspace`: юнит + golden-кросс-валидация + интеграционные (в контейнере) |
| **docker-build** | Сборка образа `walking_robot_sim:ci` |
| **smoke-tests** | Запуск контейнера, проверка узлов и топиков, переключение режимов |

Rust-тесты выполняются внутри контейнера: там ROS-окружение и собранный
`rclrs`. Golden-данные C++-эталона завендорены в
`src/quadropted_controller_rust/quadropted-core/tests/golden/mod.rs`,
поэтому C++-пакет для прогона не нужен.

---

## Локальные проверки

```bash
# Линтинг
make ci-lint
make ci-lint-yaml
make ci-lint-python

# Rust-тесты (юнит + golden-кросс-валидация + интеграционные)
make test-rust

# Скрипт напрямую (в контейнере; --host — локально)
./scripts/test_cross_validation.sh
```

---

## Конфигурация

- `.github/workflows/ci.yml` — CI workflow
- `.yamllint` — конфиг yamllint
- `makefiles/ci.mk` — локальные линт-цели
- `makefiles/test.mk` — локальные тест-цели

---

## Разработка

Для добавления нового шага в CI:
1. Отредактировать `.github/workflows/ci.yml`
2. Убедиться, что шаг выполняется внутри собранного Docker-контейнера
3. Проверить локально через `make ci-*` или `make test-*`

Для добавления интеграционного теста:
1. Добавить тест в `src/quadropted_controller_rust` или скрипт в `src/tests/`
2. Добавить шаг в `.github/workflows/ci.yml` (job `rust-tests` или `smoke-tests`)

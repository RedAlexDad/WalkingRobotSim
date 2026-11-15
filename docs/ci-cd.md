# CI/CD

Пайплайн GitHub Actions: `.github/workflows/ci-cd.yml`, workflow **CI/CD**.

Цепочка job'ов:
`lint → tests (Rust + покрытие) → publish (GHCR, только main) → release (GitHub Release, только main)`.

---

## Workflow: CI/CD

Триггеры: `push` в `main`, `jazzy_cpp`, `feat/rust-*`; `pull_request`
в `main`; ручной `workflow_dispatch`.

| Job | Когда | Описание |
|-----|-------|----------|
| **lint** | всегда | yamllint (`workflow-файлы`, `src/docker/*.yml`) + ruff для `src/`. Advisory (`continue-on-error`): pre-existing ruff-долг не блокирует автотесты и релиз |
| **tests** | после `lint` | сборка контейнера, `cargo test --workspace` (юнит + golden-кросс-валидация + интеграционные), `cargo llvm-cov` с порогом 90% строк; отчёт (lcov/html/cobertura) в artifact `rust-coverage` |
| **publish** | **только `main`**, после `tests` | сборка и публикация образа в GitHub Packages (GHCR) с тегами `latest`, `<sha>`, `v0.1.<run_number>`; registry-кэш слоёв |
| **release** | **только `main`**, после `publish` | GitHub Release `v0.1.<run_number>` с автоматическими notes и ссылкой на образ/digest |

Публикация в GHCR и релиз выполняются только на `main` и строго после
успешных автотестов. На остальных ветках и в PR прогоняются только
`lint` и `tests`.

Rust-тесты выполняются внутри контейнера: там ROS-окружение и собранный
`rclrs`. Golden-данные C++-эталона завендорены в
`src/quadropted_controller_rust/quadropted-core/tests/golden/mod.rs`,
поэтому C++-пакет для прогона не нужен.

Локальный кэш образа (`images/*.tar.zst`) и его восстановление описаны в
[`src/docker/README.md`](../src/docker/README.md).

---

## Локальные проверки

```bash
# Линтинг
make ci-lint
make ci-lint-yaml
make ci-lint-python

# Rust-тесты (юнит + golden-кросс-валидация + интеграционные)
make test-rust

# Покрытие (llvm-cov, порог 90% строк; отчёт в reports/coverage)
make test-coverage-rust

# Скрипт напрямую (в контейнере; --host — локально)
./scripts/test_cross_validation.sh
```

---

## Конфигурация

- `.github/workflows/ci-cd.yml` — пайплайн CI/CD (lint → tests → publish → release)
- `.yamllint` — конфиг yamllint
- `makefiles/ci.mk` — локальные линт-цели
- `makefiles/test.mk` — локальные тест-цели
- `makefiles/docker.mk` — сборка, `images/`-кэш и GHCR (`image-pull`, `image-restore`)

---

## Разработка

Для добавления нового шага в CI:
1. Отредактировать `.github/workflows/ci-cd.yml`
2. Убедиться, что шаг выполняется внутри собранного Docker-контейнера
3. Проверить локально через `make ci-*` или `make test-*`

Для добавления интеграционного теста:
1. Добавить тест в `src/quadropted_controller_rust` или скрипт в `src/tests/`
2. Добавить шаг в `.github/workflows/ci-cd.yml` (job `tests`)

# CI/CD

Пайплайн GitHub Actions: `.github/workflows/ci-cd.yml`, workflow **CI/CD**.

Ключевая идея: **образ собирается ровно один раз** (`build-image`), а дальше
передаётся между job'ами zstd-артефактом (`docker-image`, ~3.4 ГБ вместо 16 ГБ
image). Поэтому `tests`, `coverage` и `smoke` работают параллельно на одном
образе, а публикация в GHCR не пересобирает его заново.

```
changes ─┬─ lint (advisory)
         └─ build-image ─┬─ tests      ─┐
                         ├─ coverage    ├─ publish (main) ─ release (main)
                         └─ smoke      ─┘
```

---

## Job'ы

| Job | Когда | Описание |
|-----|-------|----------|
| **changes** | всегда | Определяет, менялся ли код (`src/`, `scripts/`, `makefiles/`, `Makefile`, `compose*.yml`, workflows). На правках только документации тяжёлые job'ы пропускаются |
| **lint** | всегда | yamllint (workflows + compose), ruff, hadolint (Dockerfile), shellcheck. Advisory (`continue-on-error`): ruff-долг не блокирует автотесты и релиз |
| **build-image** | код изменился | Единственная сборка Docker-образа; `make image-save` кладёт zstd-архив в `images/`, он уходит артефактом `docker-image` (retention 3 дня) |
| **tests** | после build-image | Скачивает артефакт, `make image-load`, поднимает контейнер, `cargo test --workspace`: юнит + golden-кросс-валидация + интеграционные |
| **coverage** | после build-image | Скачивает артефакт, `cargo llvm-cov` по workspace, порог **90% строк**; отчёт (lcov/html/cobertura) в артефакт `rust-coverage` |
| **smoke** | после build-image | Запуск контейнера: узлы, топики, переключение режимов (`TROT/CRAWL/STAND/REST`), velocity; результаты в артефакт `smoke-results` |
| **publish** | **только `main`**, после tests+coverage+smoke | Скачивает артефакт, тегирует и пушит в GHCR (`latest`, `<sha>`, `v0.1.<run_number>`) **без пересборки**; публикует digest |
| **release** | **только `main`**, после publish | GitHub Release `v0.1.<run_number>`: авто-notes + ссылки на образ и digest |

Триггеры: `push` в `main`, `jazzy_cpp`, `feat/rust-*`; `pull_request`
в `main`; ручной `workflow_dispatch`. Устаревшие прогоны на той же ветке
отменяются (`concurrency.cancel-in-progress`).

Rust-тесты выполняются внутри контейнера: там ROS-окружение и собранный
`rclrs`. Golden-данные C++-эталона завендорены в
`src/quadropted_controller_rust/quadropted-core/tests/golden/mod.rs`,
поэтому C++-пакет для прогона не нужен.

Локальный кэш образа (`images/*.tar.zst`) и восстановление после
`docker purge` описаны в [`src/docker/README.md`](../src/docker/README.md).

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

# Кэш образа: сохранить/загрузить/скачать из GHCR
make image-save
make image-load
make image-pull
```

---

## Конфигурация

- `.github/workflows/ci-cd.yml` — пайплайн CI/CD
- `.yamllint` — конфиг yamllint
- `makefiles/ci.mk` — локальные линт-цели
- `makefiles/test.mk` — локальные тест-цели
- `makefiles/docker.mk` — сборка, `images/`-кэш и GHCR (`image-save/load/pull/restore`)

---

## Разработка

Добавление шага в CI:
1. Отредактировать `.github/workflows/ci-cd.yml`
2. Шаги, которым нужен образ, выполняются после `Download image artifact`
   и `make image-load` (а не пересобирают образ)
3. Проверить локально через `make ci-*`, `make test-*`, `make image-*`

Добавление интеграционного теста:
1. Добавить тест в `src/quadropted_controller_rust` или скрипт в `src/tests/`
2. Добавить шаг в `.github/workflows/ci-cd.yml` (job `tests` или `smoke`)

Добавление нового артефакта/отчёта:
1. Складывать в `reports/` (не в git)
2. Публиковать через `actions/upload-artifact`

Публикация и релиз выполняются только на `main` и только после успешных
`tests`, `coverage` и `smoke`.

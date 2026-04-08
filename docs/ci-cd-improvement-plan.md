# План улучшения CI/CD и тестирования

**Дата:** 2026-04-08  
**Цель:** Создать надёжный, быстрый и информативный CI/CD пайплайн для WalkingRobotSim

---

## Текущее состояние

| Компонент | Статус | Проблемы |
|-----------|--------|----------|
| `ci.yml` | ✅ Есть | Только Docker build, `--no-cache`, `sleep 30` |
| `test.yml` | ⚠️ Дублирует ci.yml | Долгие sleep, всегда success, нет fail при проблемах |
| C++ тесты | ✅ colcon test | Не запускаются в CI, только локально |
| Python тесты | ❌ Нет | Нет тестов для Python контроллеров |
| Linting | ❌ Нет | Нет ruff, flake8, clang-format, yamllint |
| Docker cache | ❌ Нет | `--no-cache` каждый раз — медленная сборка |
| Artifacts | ✅ Есть | Логи сохраняются, но без анализа |
| Branch protection | ❌ Нет | Можно пушить без проверок |
| Tags/Releases | ⚠️ Есть тег v0.0.2 | Нет авто-релизов |

---

## Архитектура нового пайплайна

```
push/PR
  │
  ├─→ [1] Lint & Static Analysis (2-3 min)
  │       ├─ Python: ruff, flake8
  │       ├─ C++: clang-format check, cppcheck
  │       ├─ YAML: yamllint
  │       └─ Makefile: syntax check
  │
  ├─→ [2] C++ Unit Tests (10-15 min)
  │       ├─ Install ROS 2 Jazzy (apt)
  │       ├─ colcon build
  │       ├─ colcon test
  │       └─ Upload coverage
  │
  ├─→ [3] Docker Build (20-40 min, cached: 5-10 min)
  │       ├─ Build with layer cache
  │       ├─ Verify image size < 15GB
  │       └─ Save build artifact
  │
  └─→ [4] Docker Smoke Tests (5-10 min)
          ├─ Start container
          ├─ Wait for ROS nodes (poll, not sleep)
          ├─ Check critical nodes
          ├─ Check critical topics
          ├─ Test behavior state switching (REST↔TROT↔STAND)
          └─ Cleanup
```

---

## Декомпозиция задач

### Фаза 1: Lint & Static Analysis

| # | Задача | Файл | Описание | Приоритет |
|---|--------|------|----------|-----------|
| 1.1 | Добавить yamllint для workflow | `.github/workflows/ci.yml` | Проверка синтаксиса всех `.yml` файлов | 🔴 High |
| 1.2 | Добавить ruff для Python | `.github/workflows/ci.yml` | Быстрый линтер Python кода | 🔴 High |
| 1.3 | Добавить clang-format check | `.github/workflows/ci.yml` | Проверка стиля C++ кода | 🟡 Medium |
| 1.4 | Добавить flake8 для legacy Python | `.github/workflows/ci.yml` | Линтер для старых `.py` скриптов | 🟢 Low |
| 1.5 | Добавить concurrency group | `.github/workflows/ci.yml` | Отмена старых ранов при новом push | 🔴 High |

### Фаза 2: C++ Unit Tests в CI

| # | Задача | Файл | Описание | Приоритет |
|---|--------|------|----------|-----------|
| 2.1 | Установить ROS 2 Jazzy в CI | `.github/workflows/ci.yml` | apt install ros-jazzy-ros-base + deps | 🔴 High |
| 2.2 | colcon build в CI | `.github/workflows/ci.yml` | Сборка C++ пакета | 🔴 High |
| 2.3 | colcon test в CI | `.github/workflows/ci.yml` | Запуск unit тестов | 🔴 High |
| 2.4 | Upload test results | `.github/workflows/ci.yml` | Артефакты с XML результатами | 🟡 Medium |
| 2.5 | Docker-based colcon test (fallback) | `.github/workflows/ci.yml` | Тесты внутри Docker если apt не работает | 🟡 Medium |

### Фаза 3: Docker Build Optimization

| # | Задача | Файл | Описание | Приоритет |
|---|--------|------|----------|-----------|
| 3.1 | Убрать `--no-cache` | `ci.yml`, `test.yml` | Использовать Docker layer cache | 🔴 High |
| 3.2 | Добавить actions/cache для Buildx | `.github/workflows/ci.yml` | Кэширование слоёв между раннами | 🔴 High |
| 3.3 | Multi-stage build verification | `.github/workflows/ci.yml` | Проверка что multi-stage работает | 🟡 Medium |
| 3.4 | Image size check | `.github/workflows/ci.yml` | Fail если образ > 15GB | 🟢 Low |

### Фаза 4: Docker Smoke Tests

| # | Задача | Файл | Описание | Приоритет |
|---|--------|------|----------|-----------|
| 4.1 | Poll-based ROS wait | `.github/workflows/ci.yml` | Заменить `sleep 90` на цикл с проверкой nodes | 🔴 High |
| 4.2 | Critical nodes check | `.github/workflows/ci.yml` | Проверка robot_controller, odometry, cmd_vel_pub | 🔴 High |
| 4.3 | Critical topics check | `.github/workflows/ci.yml` | Проверка /robot1/joint_states, /robot1/odom, /robot1/imu | 🔴 High |
| 4.4 | Behavior state switching | `.github/workflows/ci.yml` | Тест REST→TROT→STAND→REST переключений | 🔴 High |
| 4.5 | Timeout для каждого шага | `.github/workflows/ci.yml` | Не более 10 min на шаг | 🟡 Medium |
| 4.6 | Cleanup on failure | `.github/workflows/ci.yml` | `docker compose down` даже при fail | 🔴 High |

### Фаза 5: Workflow Organization

| # | Задача | Файл | Описание | Приоритет |
|---|--------|------|----------|-----------|
| 5.1 | Удалить `test.yml` | `.github/workflows/test.yml` | Дублирует `ci.yml`, убрать | 🔴 High |
| 5.2 | Consolidate в единый `ci.yml` | `.github/workflows/ci.yml` | Один файл с 4 jobs | 🔴 High |
| 5.3 | Добавить `workflow_dispatch` | `.github/workflows/ci.yml` | Ручной запуск из GitHub UI | 🟡 Medium |
| 5.4 | Matrix testing (optional) | `.github/workflows/ci.yml` | Тест на ubuntu-latest + ubuntu-22.04 | 🟢 Low |

### Фаза 6: Advanced (будущие улучшения)

| # | Задача | Файл | Описание | Приоритет |
|---|--------|------|----------|-----------|
| 6.1 | Code coverage | `.github/workflows/ci.yml` | gcov/lcov для C++ coverage | 🟡 Medium |
| 6.2 | Auto-release on tag | `.github/workflows/release.yml` | Создание GitHub Release при теге | 🟡 Medium |
| 6.3 | Branch protection rules | GitHub settings | Require CI pass before merge | 🟡 Medium |
| 6.4 | PR comment with results | GitHub Action | Комментировать PR с результатами тестов | 🟢 Low |
| 6.5 | Slack/Discord notification | GitHub Action | Уведомления о fail | 🟢 Low |
| 6.6 | Performance benchmark | `.github/workflows/benchmark.yml` | Запуск benchmark.cpp и сравнение | 🟢 Low |

---

## Итоговый чек-лист

### Обязательные (блокерируют merge)
- [ ] 1.1 yamllint для workflow файлов
- [ ] 1.2 ruff для Python кода
- [ ] 1.5 Concurrency groups
- [ ] 2.2 colcon build в CI
- [ ] 2.3 colcon test в CI
- [ ] 3.1 Убрать `--no-cache`
- [ ] 3.2 Buildx cache
- [ ] 4.1 Poll-based ROS wait
- [ ] 4.2 Critical nodes check
- [ ] 4.3 Critical topics check
- [ ] 4.4 Behavior state switching test
- [ ] 4.6 Cleanup on failure
- [ ] 5.1 Удалить `test.yml`
- [ ] 5.2 Consolidate в единый `ci.yml`

### Рекомендованные (не блокерируют)
- [ ] 1.3 clang-format check
- [ ] 1.4 flake8 для legacy Python
- [ ] 2.4 Upload test results
- [ ] 2.5 Docker-based colcon test (fallback)
- [ ] 3.3 Multi-stage build verification
- [ ] 3.4 Image size check
- [ ] 4.5 Timeout для каждого шага
- [ ] 5.3 workflow_dispatch
- [ ] 6.1 Code coverage
- [ ] 6.2 Auto-release on tag

### Опциональные (будущие итерации)
- [ ] 5.4 Matrix testing
- [ ] 6.3 Branch protection rules
- [ ] 6.4 PR comment with results
- [ ] 6.5 Slack/Discord notification
- [ ] 6.6 Performance benchmark

---

## Метрики успеха

| Метрика | Было | Станет |
|---------|------|--------|
| Время lint | ❌ 0 min | ✅ 2-3 min |
| Время C++ test | ❌ 0 min | ✅ 10-15 min |
| Время Docker build | 40-60 min (no cache) | ✅ 5-10 min (cached) |
| Время smoke test | 5-10 min | ✅ 5 min |
| **Общее время** | 45-70 min | ✅ 20-35 min |
| Fail при broken code | ❌ Нет | ✅ Да |
| Fail при broken Docker | ❌ Нет | ✅ Да |
| Тест STAND режима | ❌ Нет | ✅ Да |
| Артефакты | ✅ Частично | ✅ Полные логи + coverage |

---

## Изменённые файлы

| Файл | Действие |
|------|----------|
| `.github/workflows/ci.yml` | ✏️ Полная переработка |
| `.github/workflows/test.yml` | ❌ Удалить |
| `Makefile` | ✏️ Добавить `make ci-lint`, `make ci-test` |
| `test-workflows.sh` | ✏️ Обновить под новый workflow |
| `docs/ci-cd-improvement-plan.md` | 📝 Этот файл |

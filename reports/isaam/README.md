# Isaac Sim Research — WalkingRobotSim

Содержание директории `reports/isaam/`:

| Файл | Описание |
| ---- | ----------------------------------------------------------------------------------------- |
| `2026-07-17_isaac-sim-vs-gazebo-terrain-report.md` | **Главный отчёт** (1496 строк) — полный анализ Isaac Sim vs Gazebo для симуляции рельефа |
| `2026-07-18_migration-gazebo-to-isaac-plan.md` | **План миграции** — пошаговый переход с Gazebo на Isaac Sim с сохранением elevation mapping |
| `2026-07-18_rust-isaac-integration.md` | **Rust + Isaac Sim** — интеграция rclrs-контроллера с Isaac Sim через Python bridge |
| `2026-08-22_docker-microservices-v2.md` | **План декомпозиции монолита на микросервисы (v2)** — gazebo-sim + wrs-core + wrs-nav2 + wrs-rviz, Isaac Sim нативно |
| `2026-08-22_simulation-issues-report.md` | **Отчёт о развёртывании и проблемах симуляции** — Часть A (деплой) + Часть B (5 проблем по цепочке Симптом→Гипотезы→Причина→Решение) |
| `2026-08-23_isaac-sim-integration-report.md` | **Отчёт о развёртывании и проблемах Isaac Sim** — Часть A (мост Rust↔Isaac, полный цикл) + Часть B (11 проблем: память, rclpy-конфликт, коллизия, QoS, setDriveTarget, foot_contact) |
| `checklist-install.md` | Пошаговый чек-лист установки Isaac Sim |
| `quick-reference.md` | Быстрый справочник команд и параметров |

## Статус

- Основной план миграции Gazebo → Isaac Sim: ветка `feat/isaam-research`
  (`2026-07-18_migration-gazebo-to-isaac-plan.md`)
- Отчёт про Rust-интеграцию: ветка `feat/rust-migration`
  (`2026-07-18_rust-isaac-integration.md`)
- Дата: 2026-07-18 (обновлено 2026-08-23)
- Система: Lenovo Lecoo Pro 14 N155A + RTX 5070 Ti (OCuLink)
- OS: Ubuntu 24.04.4 LTS → 26.04 (Resolute)
- Isaac Sim: 6.0.1.0 в `~/isaacsim-venv`
- CUDA: 12.8.93

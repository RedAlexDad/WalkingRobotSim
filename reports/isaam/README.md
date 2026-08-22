# Isaac Sim Research — WalkingRobotSim

Содержание директории `reports/isaam/`:

| Файл | Описание |
| ---- | ----------------------------------------------------------------------------------------- |
| `2026-07-17_isaac-sim-vs-gazebo-terrain-report.md` | **Главный отчёт** (1496 строк) — полный анализ Isaac Sim vs Gazebo для симуляции рельефа |
| `2026-07-18_migration-gazebo-to-isaac-plan.md` | **План миграции** — пошаговый переход с Gazebo на Isaac Sim с сохранением elevation mapping |
| `2026-07-18_rust-isaac-integration.md` | **Rust + Isaac Sim** — интеграция rclrs-контроллера с Isaac Sim через Python bridge |
| `checklist-install.md` | Пошаговый чек-лист установки Isaac Sim |
| `quick-reference.md` | Быстрый справочник команд и параметров |

## Статус

- Основной план миграции Gazebo → Isaac Sim: ветка `feat/isaam-research`
  (`2026-07-18_migration-gazebo-to-isaac-plan.md`)
- Отчёт про Rust-интеграцию: ветка `feat/rust-migration`
  (`2026-07-18_rust-isaac-integration.md`)
- Дата: 2026-07-18
- Система: Lenovo Lecoo Pro 14 N155A + RTX 5070 Ti (OCuLink)
- OS: Ubuntu 24.04.4 LTS
- Isaac Sim: 6.0.1.0 в `~/isaacsim-venv`
- CUDA: 12.8.93

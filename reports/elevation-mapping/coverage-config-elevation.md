# Report 2026-06-09 173352 MSK

**Branch:** feat/elevation-mapping
**Stats:** 1 file changed, 3 insertions(+), 1 deletion(-)

## Что было добавлено

- Coverage-флаг `--cov=.. --cov-report=term` в `make elevation-test`
- Убран `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` — он блокировал загрузку pytest-cov

## Что было изменено

- `makefiles/elevation.mk` — pytest запускается с `--cov`, выводит таблицу покрытия

## Проблемы

- `make elevation-test` падал: `unrecognized arguments: --cov=..` — `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` отключал autodiscovery плагинов, включая pytest-cov

## Как были решены

- Убран `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` (тесты работают без него — 477 passed, 0 failed)

## Что нужно учитывать в будущем

- Текущее покрытие: **71%**. Главная причина — `elevation_mapping_node.py` (513 строк, 0%)
- Для адекватной оценки стоит исключить `*_node.py`, `conftest.py`, `test_*` из coverage

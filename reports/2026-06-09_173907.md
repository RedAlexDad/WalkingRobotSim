# Report 2026-06-09 173907 MSK

**Branch:** feat/elevation-mapping
**Stats:** 1 file changed, 6 insertions(+)

## Что было добавлено
- `.coverage`, `coverage/`, `htmlcov/`, `.coverage.*` в `.gitignore`

## Что было изменено
- `.gitignore` — добавлены правила для артефактов pytest-cov

## Проблемы
- После первого запуска `make elevation-test` с `--cov` появился неотслеживаемый файл `tests/.coverage`

## Как были решены
- `.coverage` и сопутствующие артефакты добавлены в `.gitignore`

## Что нужно учитывать в будущем
- Для очистки coverage-файлов: `git clean -fdX .coverage`

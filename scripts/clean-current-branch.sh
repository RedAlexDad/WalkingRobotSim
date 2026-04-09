#!/bin/bash
# Скрипт для удаления Co-authored-by: Qwen-Coder и эмодзи ✅ только из текущей ветки
# Использование: ./scripts/clean-current-branch.sh

set -e

BRANCH=$(git branch --show-current)

if [ -z "$BRANCH" ]; then
  echo "ERROR: HEAD detached. Переключитесь на ветку."
  exit 1
fi

echo "=== Очистка ветки: $BRANCH ==="
echo "ВНИМАНИЕ: Это перезапишет историю текущей ветки!"
echo "После завершения потребуется: git push --force-with-lease origin $BRANCH"
echo ""

# 1. Находим самый первый коммит ветки (точка расхождения с origin/<branch>)
ORIGIN_BRANCH="origin/$BRANCH"

if git rev-parse --verify "$ORIGIN_BRANCH" >/dev/null 2>&1; then
  # Находим merge-base с удалённой веткой
  BASE=$(git merge-base HEAD "$ORIGIN_BRANCH")
  echo "Базовый коммит: $BASE"
  echo "Переписываем коммиты: $BASE..HEAD"
  RANGE="${BASE}..HEAD"
else
  echo "WARNING: $ORIGIN_BRANCH не найден. Переписываем всю историю ветки."
  # Переписываем последние 100 коммитов
  RANGE="HEAD~100..HEAD"
fi

# 2. Запускаем filter-branch только для текущей ветки
echo "Запуск filter-branch..."
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
  --msg-filter '
    # Удаляем Co-authored-by
    sed "s/Co-authored-by: Qwen-Coder <qwen-coder@alibabacloud.com>//g" |
    # Удаляем эмодзи
    sed "s/✅//g; s/⏳//g" |
    # Сохраняем ПЕРВУЮ пустую строку (разделитель subject/body), удаляем остальные trailing
    awk "
      BEGIN { line_num=0 }
      { lines[line_num++] = \$0 }
      END {
        print lines[0]
        if (line_num > 1 && lines[1] == \"\") {
          has_blank=1
        }
        if (!has_blank && line_num > 1) {
          print \"\"
        }
        for (i = 1; i < line_num; i++) {
          print lines[i]
        }
      }
    " |
    # Убираем trailing пробелы
    sed "s/  *$//"
  ' \
  "$RANGE"

# 3. Удаляем backup ссылки
echo "Удаление backup ссылок..."
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin

# 4. Очищаем reflog только для текущей ветки
echo "Очистка reflog..."
git reflog expire --expire=now "$BRANCH"

# 5. Запускаем garbage collection
echo "Запуск garbage collection..."
git gc --prune=now

# 6. Проверяем результат
echo ""
echo "=== Проверка ==="
COUNT=$(git log --format="%B" | grep -c "Co-authored-by: Qwen-Coder\|✅" || true)

if [ "$COUNT" -eq 0 ]; then
  echo "SUCCESS: Все Co-authored-by и ✅ удалены из ветки $BRANCH!"
  echo ""
  echo "Для отправки в удалённый репозиторий выполните:"
  echo "  git push --force-with-lease origin $BRANCH"
else
  echo "WARNING: Найдено $COUNT вхождений в текущей ветке"
  exit 1
fi

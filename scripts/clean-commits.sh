#!/bin/bash
# Скрипт для удаления Co-authored-by: Qwen-Coder и эмодзи ✅ из всех коммитов и тэгов
# Использование: ./scripts/clean-commits.sh

set -e

echo "=== Очистка коммитов от Co-authored-by и эмодзи ==="

# 1. Удаляем Co-authored-by и ✅ из всех коммитов и тэгов
echo "Запуск filter-branch..."
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
  --msg-filter 'sed "s/Co-authored-by: Qwen-Coder <qwen-coder@alibabacloud.com>//g; s/✅//g; /^[[:space:]]*$/d; s/  *$//"' \
  --tag-name-filter cat \
  -- --all

# 2. Удаляем оригинальные ссылки (backup от filter-branch)
echo "Удаление backup ссылок..."
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin

# 3. Очищаем reflog
echo "Очистка reflog..."
git reflog expire --expire=now --all

# 4. Удаляем мусор
echo "Запуск garbage collection..."
git gc --prune=now --aggressive

# 5. Проверяем результат
echo ""
echo "=== Проверка ==="
COUNT=$(git log --all --format="%B" | grep -c "Co-authored-by: Qwen-Coder\|✅" || true)

if [ "$COUNT" -eq 0 ]; then
  echo "SUCCESS: Все Co-authored-by и ✅ удалены!"
else
  echo "WARNING: Найдено $count вхождений, возможно остались скрытые ссылки"
  exit 1
fi

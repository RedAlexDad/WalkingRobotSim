# Паттерны для конвертации LaTeX → MyST

## 1. Escape-последовательности в `\texttt{...}`

**Проблема:** Внутри `\texttt{...}` обратная косая черта `\` должна быть экранирована как `\\`.
Без экранирования `\n`, `\t`, `\r` и т.д. интерпретируются как управляющие символы, а
одиночный `\` в конце строки ломает парсер.

**Паттерн:** Любое вхождение `\` внутри `\texttt{...}` должно быть заменено на `\\`.

**Пример:**
```diff
- \texttt{\n\t\treturn \textquotedblleft traversable\textquotedblright;}
+ \texttt{\\n\\t\\treturn \\textquotedblleft traversable\\textquotedblright;}
```

## 2. Подчёркивания внутри `\mathrm{...}`

**Проблема:** В некоторых парсерах `\_` внутри `\mathrm{...}` интерпретируется как нижний
индекс, что даёт ошибку "Double subscripts: use braces to clarify".

**Решение:** Разбить `\mathrm{word1\_word2}` на `\mathrm{word1}\_\mathrm{word2}`.

**Автоматизация:**
```python
def fix_mathrm(m):
    inner = m.group(1)
    if r'\_' in inner:
        parts = inner.split(r'\_')
        return r'\mathrm{' + r'}\_\mathrm{'.join(parts) + '}'
    return m.group(0)

content = re.sub(r'\\mathrm\{([^}]*)\}', fix_mathrm, content)
```

## 3. SI-единицы через `\si{...}`

**Проблема:** Команды `\litre`, `\per`, `\kilo`, `\gram`, `\meter`, `\second` и т.д.
не поддерживаются в LaTeX без пакета `siunitx`.

**Решение:** Заменять на компактное представление внутри `\si{...}`.

```diff
- \si{\litre\per\100\kilo\gram}
+ \si{L\cdot kg^{-1}}
```

## 4. Удаление `\usepackage[utf8]{inputenc}`

**Проблема:** В современных дистрибутивах LaTeX (2018+) `inputenc` с `utf8` является
стандартным.

**Решение:** Удалить строку целиком.

```diff
- \usepackage[utf8]{inputenc}
```

## 5. Удаление `\DeclareUnicodeCharacter`

**Проблема:** В современных движках (LuaLaTeX, XeLaTeX) Unicode-символы работают нативно.

**Решение:** Удалить строки вида `\DeclareUnicodeCharacter{...}{...}`.

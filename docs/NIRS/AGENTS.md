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

**Проблема:** GitHub markdown pre-processor преобразует `\_` → `_` внутри math-блоков.
KaTeX воспринимает `_` как оператор нижнего индекса, и цепочка вида
`\mathrm{elevation}\_\mathrm{diff}\_\mathrm{cost}` после обработки становится
`\mathrm{elevation}_\mathrm{diff}_\mathrm{cost}`, что даёт "Double subscripts".

**Решение:** Заменить многословные имена с подчёркиваниями на camelCase внутри одного
`\mathrm{...}`: `\mathrm{elevationDiffCost}` вместо `\mathrm{elevation}\_\mathrm{diff}\_\mathrm{cost}`.

**Автоматизация:**
```python
REPLACEMENTS = {
    r'\\mathrm\{map\}_\\_\mathrm\{origin\}_x': '\\mathrm{mapOrigin}_x',
    r'\\mathrm\{map\}_\\_\mathrm\{origin\}_y': '\\mathrm{mapOrigin}_y',
    r'\\mathrm\{slope\}_\\_\mathrm\{cost\}': '\\mathrm{slopeCost}',
    r'\\mathrm\{roughness\}_\\_\mathrm\{cost\}': '\\mathrm{roughnessCost}',
    r'\\mathrm\{elevation\}_\\_\mathrm\{diff\}_\\_\mathrm\{cost\}': '\\mathrm{elevationDiffCost}',
    r'\\mathrm\{max\}_\\_\mathrm\{slope\}': '\\mathrm{maxSlope}',
    r'\\mathrm\{max\}_\\_\mathrm\{roughness\}': '\\mathrm{maxRoughness}',
    r'\\mathrm\{max\}_\\_\mathrm\{elevation\}_\\_\mathrm\{diff\}': '\\mathrm{maxElevationDiff}',
    r'\\mathrm\{edge\}_\\_\mathrm\{cost\}': '\\mathrm{edgeCost}',
    r'\\mathrm\{terrain\}_\\_\mathrm\{type\}': '\\mathrm{terrainType}',
    r'\\mathrm\{path\}_\\_\mathrm\{length\}': '\\mathrm{pathLength}',
    r'\\mathrm\{travel\}_\\_\mathrm\{time\}': '\\mathrm{travelTime}',
}

for fpath in glob.glob('docs/NIRS/ch3_*.md'):
    with open(fpath) as f:
        content = f.read()
    for old, new in REPLACEMENTS.items():
        content = re.sub(old, new, content)
    with open(fpath, 'w') as f:
        f.write(content)
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

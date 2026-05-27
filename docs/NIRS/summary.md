## Goal
- Исправить формулы LaTeX в главах 3 НИРС для корректного отображения на GitHub (KaTeX)

## Constraints & Preferences
- Команды должны работать в KaTeX/GitHub
- Имена файлов и разделов должны сохраняться
- Коммиты должны быть атомарными

## Progress
### Done
- **root cause:** GitHub markdown pre-processor преобразует `\_` → `_` внутри math-блоков
- KaTeX воспринимает `_` как оператор нижнего индекса — `\mathrm{elevation}\_\mathrm{diff}\_\mathrm{cost}` становится `\mathrm{elevation}_\mathrm{diff}_\mathrm{cost}` = Double subscripts
- Заменены все `\_` между `\mathrm{...}` на camelCase имена внутри единого `\mathrm{...}` в 5 файлах:
  - `\mathrm{map}\_\mathrm{origin}_x` → `\mathrm{mapOrigin}_x`
  - `\mathrm{slope}\_\mathrm{cost}` → `\mathrm{slopeCost}`
  - `\mathrm{elevation}\_\mathrm{diff}\_\mathrm{cost}` → `\mathrm{elevationDiffCost}`
  - `\mathrm{terrain}\_\mathrm{type}` → `\mathrm{terrainType}`
  - `\mathrm{edge}\_\mathrm{cost}` → `\mathrm{edgeCost}`
  - `\mathrm{path}\_\mathrm{length}` → `\mathrm{pathLength}`
  - `\mathrm{travel}\_\mathrm{time}` → `\mathrm{travelTime}`
  - `\mathrm{max}\_\mathrm{slope}` → `\mathrm{maxSlope}`
  - `\mathrm{max}\_\mathrm{roughness}` → `\mathrm{maxRoughness}`
  - `\mathrm{max}\_\mathrm{elevation}\_\mathrm{diff}` → `\mathrm{maxElevationDiff}`
- Обновлён AGENTS.md с правильным решением и автоматизацией
- Коммит `9901382` (6 файлов, 40 insertions, 23 deletions)

### In Progress
- (none)

### Blocked
- Ожидает проверки на GitHub: ошибка "Double subscripts" должна исчезнуть, т.к. в формулах больше нет `\_` (только `_` для intentional subscript `cell_x`, `foot_x`, `w_{\mathrm{slope}}` и т.д.)

## Key Decisions
- Вместо `\_` (который слопается GitHub pre-processor'ом) → camelCase внутри `\mathrm{...}`
- Второе решение (вынесение `\_` между `\mathrm{...}`) тоже не работает — GitHub превращает `\_` → `_` → KaTeX видит subscript

## Next Steps
- Пушнуть коммит на GitHub и проверить отображение

## Relevant Files
- `/home/redalexdad/GitHub/WalkingRobotSim/docs/NIRS/ch3_08_dem.md` — `mapOrigin`
- `/home/redalexdad/GitHub/WalkingRobotSim/docs/NIRS/ch3_09_cost.md` — `slopeCost`, `roughnessCost`, `elevationDiffCost`, `maxSlope`, `maxRoughness`, `maxElevationDiff`, `edgeCost`
- `/home/redalexdad/GitHub/WalkingRobotSim/docs/NIRS/ch3_10_gait.md` — `mapOrigin`, `terrainType`
- `/home/redalexdad/GitHub/WalkingRobotSim/docs/NIRS/ch3_12_metrics.md` — `pathLength`, `travelTime`
- `/home/redalexdad/GitHub/WalkingRobotSim/docs/NIRS/ch3_13_conclusions.md` — `slopeCost`, `roughnessCost`, `elevationDiffCost`
- `/home/redalexdad/GitHub/WalkingRobotSim/docs/NIRS/AGENTS.md` — patterns (updated)

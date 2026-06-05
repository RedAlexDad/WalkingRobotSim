# Report 2026-06-05 12:59:28 MSK

**Branch:** feat/elevation-mapping
**Stats:** 5 files changed, 200 insertions(+), 201 deletions(-)

## What was changed
- `src/gazebo_sim/config/nav2_params.yaml` — убраны явные `map_topic: "/robot1/map"` из static_layer (назначался через namespace)
- `src/gazebo_sim/config/robots.yaml` — убран `Y_pose` (не использовался)
- `src/gazebo_sim/launch/gazebo_multi_nav2_cpp.launch.py` — закомментирован `-Y` аргумент спавна
- `src/gazebo_sim/launch/nav2/localization_launch.py` — возвращён `root_key=namespace`, `param_rewrites` с `yaml_filename` и `use_sim_time`, убран `ParameterFile`
- `src/gazebo_sim/launch/nav2/navigation_launch.py` — возвращён `root_key=namespace`, `ParameterFile` заменён на прямой `RewrittenYaml`
- `src/go2_description/xacro/leg.xacro` — возвращён `ros2_control` блок с `gazebo_ros2_control/GazeboSystem` (удалён ранее, восстановлен)

## Problems encountered
- После переписывания launch-файлов под стандарт nav2_bringup (ParameterFile + root_key=namespace) costmap static_layer перестал получать карту. Плагин не инициализировался — не появлялось сообщение "Using plugin static_layer"
- Причина не выяснена до конца, но откат к рабочей конфигурации (root_key=namespace + RewrittenYaml без ParameterFile) решил проблему

## How they were solved
- Полный откат `src/gazebo_sim/` до коммита `9c1eb44` — последней версии, где Nav2 работал корректно
- `leg.xacro` восстановлен до оригинального `gazebo_ros2_control/GazeboSystem` (удаление ros2_control блока могло вызвать нестабильность)

## Notes for the future
- При переписывании launch-файлов нужно тестировать не только map_server, но и costmap static_layer
- ParameterFile с allow_substs=True может мешать загрузке параметров плагинов costmap

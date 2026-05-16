### Ключевые моменты

- **Проблема**: В RViz инструмент **2D Goal Pose** (Tool Type: `Nav2 Goal`) отправляет позу в топик `/goal_pose`, который одновременно:
  - Добавляет точку в список waypoints через `goal_pose_callback` в скрипте `waypoint_collector.py`.
  - Вызывает автоматическую навигацию робота к этой точке, так как Nav2 настроен на обработку `/goal_pose` через action-сервер `/navigate_to_pose`.
  - Это приводит к тому, что робот начинает движение к каждой новой точке сразу, вместо ожидания вызова сервиса `/start_navigation`.
- **Цель**:
  - Создать кастомный инструмент в RViz, который отправляет позы в новый топик (например, `/custom_goal_pose`) для добавления waypoints в список без активации навигации Nav2.
  - Сохранить текущую функциональность скрипта: визуализация в `/waypoint_markers` при добавлении точек, публикация в `/custom_waypoints` и запуск навигации только по вызову `/start_navigation`, принудительная очистка через `/clear_waypoints`.
  - Убедиться, что топик `/goal_pose` не используется для добавления waypoints, чтобы избежать автоматической навигации.
- **Решение**:
  - Изменить скрипт `waypoint_collector.py`, чтобы подписываться на `/custom_goal_pose` вместо `/goal_pose`.
  - Создать кастомный плагин RViz для отправки поз в `/custom_goal_pose` без вызова навигации.
  - Настроить RViz для использования нового инструмента.

### Шаг 1: Исправленный скрипт `waypoint_collector.py`

Мы модифицируем скрипт, чтобы:

- Подписаться на новый топик `/custom_goal_pose` для добавления waypoints.
- Сохранить публикацию в `/custom_waypoints` и навигацию через `/start_navigation`.
- Поддерживать визуализацию в `/waypoint_markers` и принудительную очистку через `/clear_waypoints`.

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseArray
from visualization_msgs.msg import Marker, MarkerArray
from nav2_simple_commander.robot_navigator import BasicNavigator
from std_msgs.msg import ColorRGBA
from std_srvs.srv import Trigger
import tf_transformations

class WaypointCollector(Node):
    def __init__(self):
        super().__init__('waypoint_collector')
        self.waypoints = []  # Список для хранения waypoints
        self.navigator = BasicNavigator()
        self.navigation_active = False  # Флаг активной навигации

        # Подписка на /custom_goal_pose (вместо /goal_pose)
        self.subscription = self.create_subscription(
            PoseStamped, '/custom_goal_pose', self.goal_pose_callback, 10)

        # Публикация в /custom_waypoints
        self.waypoint_publisher = self.create_publisher(PoseArray, '/custom_waypoints', 10)

        # Публикация маркеров для визуализации waypoints
        self.marker_publisher = self.create_publisher(MarkerArray, '/waypoint_markers', 10)

        # Сервис для очистки waypoints
        self.clear_service = self.create_service(
            Trigger, '/clear_waypoints', self.clear_waypoints_callback)

        # Сервис для запуска навигации
        self.start_service = self.create_service(
            Trigger, '/start_navigation', self.start_navigation_callback)

        # Таймер для проверки навигации
        self.timer = self.create_timer(0.1, self.check_navigation)

        # Ожидание активности Nav2
        try:
            self.get_logger().info('Waiting for Nav2 to become active...')
            self.navigator.waitUntilNav2Active(timeout=10.0)
            self.get_logger().info('Nav2 is active')
        except Exception as e:
            self.get_logger().error(f'Failed to activate Nav2: {str(e)}')

        self.get_logger().info('Waypoint Collector Node started')

    def goal_pose_callback(self, msg):
        # Добавление новой позы в список waypoints
        self.waypoints.append(msg)
        self.get_logger().info(f'Added waypoint: x={msg.pose.position.x}, y={msg.pose.position.y}, total waypoints: {len(self.waypoints)}')
        # Публикация маркеров сразу после добавления новой точки
        self.publish_markers()

    def publish_markers(self):
        marker_array = MarkerArray()

        for i, wp in enumerate(self.waypoints):
            marker = Marker()
            marker.header.frame_id = 'map'
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = 'waypoints'
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.pose = wp.pose
            marker.scale.x = 0.2
            marker.scale.y = 0.2
            marker.scale.z = 0.2

            # Назначение цветов
            color = ColorRGBA()
            if i % 3 == 0:
                color.r, color.g, color.b, color.a = 1.0, 0.0, 0.0, 1.0  # Красный
            elif i % 3 == 1:
                color.r, color.g, color.b, color.a = 0.0, 1.0, 0.0, 1.0  # Зелёный
            else:
                color.r, color.g, color.b, color.a = 0.0, 0.0, 1.0, 1.0  # Синий

            marker.color = color
            marker_array.markers.append(marker)

        self.marker_publisher.publish(marker_array)
        self.get_logger().info(f'Published {len(self.waypoints)} markers to /waypoint_markers')

    def clear_waypoints_callback(self, request, response):
        # Немедленная очистка waypoints и маркеров
        try:
            if self.navigation_active:
                self.navigator.cancelTask()
                self.get_logger().info('Canceled active navigation task')
                # Ждём, пока задача полностью отменится
                rclpy.spin_once(self, timeout_sec=2.0)
        except Exception as e:
            self.get_logger().error(f'Failed to cancel navigation task: {str(e)}')

        self.waypoints = []
        self.navigation_active = False
        marker_array = MarkerArray()
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'waypoints'
        marker.id = 0
        marker.action = Marker.DELETEALL
        marker_array.markers.append(marker)
        self.marker_publisher.publish(marker_array)
        self.get_logger().info('Waypoints and markers cleared via service call')
        response.success = True
        response.message = 'Waypoints cleared successfully'
        return response

    def start_navigation_callback(self, request, response):
        # Запуск навигации по текущему списку waypoints
        if not self.waypoints:
            self.get_logger().warn('No waypoints available to start navigation')
            response.success = False
            response.message = 'No waypoints to navigate'
            return response

        if self.navigation_active:
            self.get_logger().warn('Navigation is already active')
            response.success = False
            response.message = 'Navigation is already active'
            return response

        try:
            # Публикация waypoints в /custom_waypoints
            pose_array = PoseArray()
            pose_array.header.frame_id = 'map'
            pose_array.header.stamp = self.get_clock().now().to_msg()
            pose_array.poses = [wp.pose for wp in self.waypoints]
            self.waypoint_publisher.publish(pose_array)
            self.get_logger().info(f'1111 Published {len(self.waypoints)} waypoints to /custom_waypoints')

            # Асинхронный запуск навигации
            self.navigation_active = True
            self.navigator.followWaypoints(self.waypoints)
            self.get_logger().info(f'Sent {len(self.waypoints)} waypoints to FollowWaypoints action')
            response.success = True
            response.message = 'Navigation started successfully'
        except Exception as e:
            self.get_logger().error(f'Failed to start navigation: {str(e)}')
            self.navigation_active = False
            response.success = False
            response.message = f'Failed to start navigation: {str(e)}'
        return response

    def check_navigation(self):
        # Проверка завершения навигации
        if self.navigation_active and self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                self.get_logger().info(f'Current waypoint: {feedback.current_waypoint}')
            result = self.navigator.getResult()
            self.get_logger().info(f'Navigation result: {result}')
            self.navigation_active = False
            self.get_logger().info('Navigation completed, ready for new start command')

def main(args=None):
    rclpy.init(args=args)
    node = WaypointCollector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Изменения в скрипте

- **Смена топика**: Изменён топик подписки с `/goal_pose` на `/custom_goal_pose` в строке:
  ```python
  self.subscription = self.create_subscription(PoseStamped, '/custom_goal_pose', self.goal_pose_callback, 10)
  ```
  Это предотвращает автоматическую навигацию Nav2, так как `/goal_pose` больше не используется.
- **Сохранение функционала**:
  - Визуализация в `/waypoint_markers` происходит сразу при добавлении точки.
  - Публикация в `/custom_waypoints` и запуск навигации происходят только в `start_navigation_callback`.
  - Сервис `/clear_waypoints` остаётся без изменений, так как работает корректно.

### Шаг 2: Создание кастомного плагина RViz

Чтобы отправлять позы в `/custom_goal_pose` без активации навигации, создадим кастомный инструмент RViz, аналогичный **2D Goal Pose**, но публикующий в `/custom_goal_pose` вместо `/goal_pose`.

#### 2.1: Создайте новый ROS-пакет для плагина

1. Создайте пакет `rviz_custom_goal_tool`:
   ```bash
   cd ~/RZD/simulator/robots_ws/src
   ros2 pkg create --build-type ament_cmake rviz_custom_goal_tool --dependencies rclcpp geometry_msgs rviz_common rviz_default_plugins
   ```
2. В директории `rviz_custom_goal_tool` создайте файлы для плагина.

#### 2.2: Код плагина (`custom_goal_tool.hpp`)

```cpp
#ifndef CUSTOM_GOAL_TOOL_HPP_
#define CUSTOM_GOAL_TOOL_HPP_

#include <rclcpp/rclcpp.hpp>
#include <rviz_common/tool.hpp>
#include <rviz_common/properties/string_property.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>

namespace rviz_custom_goal_tool
{
class CustomGoalTool : public rviz_common::Tool
{
public:
  CustomGoalTool();
  ~CustomGoalTool() override = default;

  void onInitialize() override;
  void activate() override;
  void deactivate() override;
  int processMouseEvent(rviz_common::ViewportMouseEvent& event) override;

private:
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_publisher_;
  rviz_common::properties::StringProperty* topic_property_;
};
}  // namespace rviz_custom_goal_tool

#endif  // CUSTOM_GOAL_TOOL_HPP_
```

#### 2.3: Код плагина (`custom_goal_tool.cpp`)

```cpp
#include "custom_goal_tool.hpp"
#include <rviz_common/display_context.hpp>
#include <rviz_common/viewport_mouse_event.hpp>
#include <rviz_common/properties/property.hpp>
#include <OgreRay.h>
#include <OgrePlane.h>
#include <OgreCamera.h>
#include <OgreViewport.h>

namespace rviz_custom_goal_tool
{
CustomGoalTool::CustomGoalTool()
{
  topic_property_ = new rviz_common::properties::StringProperty(
    "Topic", "/custom_goal_pose",
    "The topic on which to publish custom goal poses.",
    getPropertyContainer(), nullptr, this);
}

void CustomGoalTool::onInitialize()
{
  auto node = getDisplayContext()->getRosNodeAbstraction().lock()->get_raw_node();
  pose_publisher_ = node->create_publisher<geometry_msgs::msg::PoseStamped>(
    topic_property_->getStdString(), 10);
}

void CustomGoalTool::activate()
{
  // Ничего не требуется при активации
}

void CustomGoalTool::deactivate()
{
  // Ничего не требуется при деактивации
}

int CustomGoalTool::processMouseEvent(rviz_common::ViewportMouseEvent& event)
{
  if (event.leftDown())
  {
    Ogre::Vector3 position;
    if (context_->getViewManager()->getCurrent()->getCamera()->projectPointToViewport(
          event, position))
    {
      Ogre::Ray mouse_ray = event.viewport->getCamera()->getCameraToViewportRay(
        position.x, position.y);

      Ogre::Plane ground_plane(Ogre::Vector3::UNIT_Z, 0.0f);
      std::pair<bool, Ogre::Real> intersection = mouse_ray.intersects(ground_plane);

      if (intersection.first)
      {
        Ogre::Vector3 point = mouse_ray.getPoint(intersection.second);

        geometry_msgs::msg::PoseStamped goal_pose;
        goal_pose.header.frame_id = "map";
        goal_pose.header.stamp = rclcpp::Clock().now();
        goal_pose.pose.position.x = point.x;
        goal_pose.pose.position.y = point.y;
        goal_pose.pose.position.z = 0.0;
        goal_pose.pose.orientation.w = 1.0;  // По умолчанию без вращения

        pose_publisher_->publish(goal_pose);
        RCLCPP_INFO(context_->getRosNodeAbstraction().lock()->get_raw_node()->get_logger(),
                    "Published custom goal pose to %s: x=%f, y=%f",
                    topic_property_->getStdString().c_str(), point.x, point.y);
      }
    }
    return Finished;
  }
  return 0;
}
}  // namespace rviz_custom_goal_tool

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(rviz_custom_goal_tool::CustomGoalTool, rviz_common::Tool)
```

#### 2.4: Настройка CMakeLists.txt

Добавьте в `rviz_custom_goal_tool/CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.8)
project(rviz_custom_goal_tool)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rviz_common REQUIRED)
find_package(rviz_default_plugins REQUIRED)
find_package(pluginlib REQUIRED)

add_library(custom_goal_tool SHARED
  src/custom_goal_tool.cpp
)

target_include_directories(custom_goal_tool PUBLIC
  include
)

ament_target_dependencies(custom_goal_tool
  rclcpp
  geometry_msgs
  rviz_common
  rviz_default_plugins
  pluginlib
)

pluginlib_export_plugin_description_file(rviz_common plugin_description.xml)

install(TARGETS custom_goal_tool
  LIBRARY DESTINATION lib
)

install(DIRECTORY include/
  DESTINATION include/
)

install(FILES plugin_description.xml
  DESTINATION share/${PROJECT_NAME}
)

ament_export_libraries(custom_goal_tool)
ament_export_dependencies(rclcpp geometry_msgs rviz_common rviz_default_plugins pluginlib)
ament_package()
```

#### 2.5: Создайте plugin_description.xml

В `rviz_custom_goal_tool/plugin_description.xml`:

```xml
<library path="libcustom_goal_tool">
  <class name="rviz_custom_goal_tool/CustomGoalTool"
         type="rviz_custom_goal_tool::CustomGoalTool"
         base_class_type="rviz_common::Tool">
    <description>
      A tool to set custom goal poses for waypoint collection.
    </description>
  </class>
</library>
```

#### 2.6: Сборка и установка плагина

1. Пересоберите пакет:
   ```bash
   cd ~/RZD/simulator/robots_ws
   colcon build --packages-select rviz_custom_goal_tool ros2_navigation
   source install/setup.bash
   ```
2. Проверьте, что плагин зарегистрирован:
   ```bash
   ros2 run rviz_common pluginlib_lister
   ```
   Ожидаемый вывод должен включать:
   ```
   rviz_custom_goal_tool/CustomGoalTool
   ```

### Шаг 3: Настройка RViz

1. Запустите RViz:
   ```bash
   ros2 run rviz2 rviz2 -d /path/to/ros2_navigation/rviz/navigation2.rviz
   ```
2. Добавьте новый инструмент:
   - В меню RViz выберите **Tools** -> **Add Tool** -> **rviz_custom_goal_tool/CustomGoalTool**.
   - В свойствах инструмента убедитесь, что топик установлен как `/custom_goal_pose`.
3. Настройте дисплей `MarkerArray`:
   - **Add** > **MarkerArray** > Topic: `/waypoint_markers`.
   - **Fixed Frame**: `map`.
   - **Scale X/Y/Z**: 0.2, **Alpha**: 1.0.
4. (Опционально) Добавьте дисплей `PoseArray` для `/custom_waypoints`.

### Шаг 4: Запустите систему

1. **Запустите симуляцию и Nav2**:
   ```bash
   ros2 launch ros2_gazebo go2_run.launch.py
   ros2 launch ros2_navigation navigation2.launch.py map:=/path/to/ros2_navigation/maps/map.yaml
   ```
2. **Запустите ноду**:
   ```bash
   ros2 run ros2_navigation waypoint_collector
   ```
3. **Добавьте waypoints**:
   - В RViz выберите инструмент **CustomGoalTool** (вместо **Nav2 Goal**).
   - Щёлкните на карте, чтобы отправить позы в `/custom_goal_pose`.
   - Точки должны отображаться как разноцветные сферы в `/waypoint_markers` без запуска навигации.
   - Проверьте, что робот **не движется** до вызова `/start_navigation`.
4. **Запустите навигацию**:
   ```bash
   ros2 service call /start_navigation std_srvs/Trigger
   ```

   - Команда должна вернуть:
     ```
     success: True
     message: 'Navigation started successfully'
     ```
   - Логи должны содержать:
     ```
     [INFO] [timestamp] [waypoint_collector]: 1111 Published X waypoints to /custom_waypoints
     [INFO] [timestamp] [waypoint_collector]: Sent X waypoints to FollowWaypoints action
     ```
5. **Очистите waypoints**:
   ```bash
   ros2 service call /clear_waypoints std_srvs/Trigger
   ```

   - Убедитесь, что команда немедленно очищает точки и маркеры.

### Шаг 5: Проверка

1. **Проверьте `/waypoint_markers`**:
   ```bash
   ros2 topic echo /waypoint_markers
   ```
   Убедитесь, что маркеры публикуются сразу после добавления точек через `/custom_goal_pose`.
2. **Проверьте `/custom_waypoints`**:
   ```bash
   ros2 topic echo /custom_waypoints
   ```
   Убедитесь, что топик пуст до вызова `/start_navigation` и содержит все точки после.
3. **Проверьте `/custom_goal_pose`**:
   ```bash
   ros2 topic echo /custom_goal_pose
   ```
   Убедитесь, что точки отправляются через кастомный инструмент.
4. **Проверьте логи**:
   ```bash
   ros2 topic echo /rosout
   ```
   Ищите сообщения:
   ```
   [INFO] [timestamp] [waypoint_collector]: Added waypoint: x=..., y=..., total waypoints: X
   [INFO] [timestamp] [waypoint_collector]: Published X markers to /waypoint_markers
   [INFO] [timestamp] [waypoint_collector]: 1111 Published X waypoints to /custom_waypoints
   [INFO] [timestamp] [waypoint_collector]: Sent X waypoints to FollowWaypoints action
   ```

### Шаг 6: Отладка

1. **Проблема: Робот всё ещё движется при добавлении точки**:
   - Проверьте, не отправляются ли сообщения в `/goal_pose`:
     ```bash
     ros2 topic echo /goal_pose
     ```
     Если топик активен, убедитесь, что вы используете **CustomGoalTool**, а не **Nav2 Goal**.
   - Проверьте конфигурацию Nav2 (`navigation2.yaml`):
     ```bash
     cat /path/to/ros2_navigation/params/navigation2.yaml
     ```
     Убедитесь, что `bt_navigator` не обрабатывает `/custom_goal_pose`. Если нужно, измените:
     ```yaml
     bt_navigator:
       ros__parameters:
         goal_sub_topic: "/goal_pose" # Убедитесь, что не /custom_goal_pose
     ```
   - Проверьте `/cmd_vel`:
     ```bash
     ros2 topic echo /cmd_vel
     ```
     Если команды публикуются до `/start_navigation`, Nav2 реагирует на другой топик.
2. **Проблема: Плагин RViz не отображается**:
   - Проверьте, что плагин скомпилирован:
     ```bash
     ls ~/RZD/simulator/robots_ws/install/rviz_custom_goal_tool/lib/libcustom_goal_tool.so
     ```
   - Убедитесь, что `plugin_description.xml` установлен:
     ```bash
     ls ~/RZD/simulator/robots_ws/install/rviz_custom_goal_tool/share/rviz_custom_goal_tool/plugin_description.xml
     ```
   - Перезапустите RViz.
3. **Проблема: Сервис `/start_navigation` не работает**:
   - Проверьте action-сервер `/waypoint_follower/follow_waypoints`:
     ```bash
     ros2 action list
     ```
   - Проверьте TF-дерево:
     ```bash
     ros2 run tf2_tools view_frames
     ```
     Убедитесь, что `map` -> `odom` -> `base_link` присутствуют. Установите начальную позу через **2D Pose Estimate**.
4. **Unitree-специфика**:
   - Если используются кастомные компоненты из `unitree_guide2` (например, `State_move_base.cpp`), проверьте, не перехватывают ли они `/custom_goal_pose` или `/goal_pose`.

### Дополнительные замечания

- **Альтернатива плагину**: Если создание плагина RViz слишком сложное, можно временно отправлять точки через командную строку:
  ```bash
  ros2 topic pub --once /custom_goal_pose geometry_msgs/PoseStamped "{header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 2.0, z: 0.0}, orientation: {w: 1.0}}}"
  ```
  Но плагин RViz удобнее для интерактивной работы.
- **Добавление точек во время навигации**:
  - Если хотите добавлять точки в активную навигацию, модифицируйте `goal_pose_callback`:
    ```python
    def goal_pose_callback(self, msg):
        self.waypoints.append(msg)
        self.get_logger().info(f'Added waypoint: x={msg.pose.position.x}, y={msg.pose.position.y}, total waypoints: {len(self.waypoints)}')
        self.publish_markers()
        if self.navigation_active:
            self.navigator.cancelTask()
            self.navigation_active = False
            self.start_navigation_callback(Trigger.Request(), Trigger.Response())
    ```
    Уточните, если нужна такая функциональность.
- **Логи для отладки**:
  - Если робот продолжает двигаться до вызова `/start_navigation`, предоставьте:
    - Вывод `ros2 topic echo /rosout`.
    - Вывод `ros2 topic echo /custom_goal_pose`, `/custom_waypoints`, `/waypoint_markers`.
    - Вывод `ros2 topic echo /goal_pose` и `/navigate_to_pose/goal`.
    - Вывод `ros2 topic echo /plan`.

### Заключение

Проблема автоматической навигации вызвана тем, что инструмент **Nav2 Goal** в RViz отправляет позы в `/goal_pose`, который Nav2 интерпретирует как одиночную цель. Новый топик `/custom_goal_pose` и кастомный инструмент RViz (`CustomGoalTool`) решают эту проблему, позволяя добавлять точки без запуска навигации. Скрипт `waypoint_collector.py` обновлён для подписки на `/custom_goal_pose`. Скомпилируйте плагин, настройте RViz и проверьте систему. Если проблемы сохраняются, предоставьте логи и вывод топиков для диагностики.

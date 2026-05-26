# Глава 3. Разработка модуля Elevation Mapping и terrain-aware планирования

## 3.5 Настройка TF и межконтейнерной связи (DDS)

### 3.5.1 Трансформации (TF)

Правильная работа elevation_mapping_node критически зависит от наличия
полного и актуального TF дерева. Модуль использует трансформации для:

- Проецирования точек облака из фрейма сенсора в фрейм карты.
- Определения положения робота на карте высот.
- Вычисления углов обзора для visibility cleanup.

**TF дерево робота Unitree Go2:**

```
map → odom → base_link → laser_frame
                        → imu_frame
                        → foot_front_left
                        → foot_front_right
                        → foot_hind_left
                        → foot_hind_right
```

Симулятор публикует эти трансформации на namespaced топиках:
- `/robot1/tf` (динамические трансформации, частота ~100 Гц)
- `/robot1/tf_static` (статические, однократно)

### 3.5.2 Разработка TF relay

Модуль elevation_mapping_cupy слушает стандартные топики `/tf` и
`/tf_static`. Для перенаправления трансформаций разработан
TF relay (`tf_relay.py`):

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

class TFRelay(Node):
    def __init__(self):
        super().__init__('tf_relay')
        
        # Подписка на /robot1/tf
        self.tf_sub = self.create_subscription(
            TFMessage, '/robot1/tf',
            self.tf_callback,
            QoSProfile(depth=100, 
                       reliability=ReliabilityPolicy.BEST_EFFORT))
        
        # Подписка на /robot1/tf_static
        self.tf_static_sub = self.create_subscription(
            TFMessage, '/robot1/tf_static',
            self.tf_static_callback,
            QoSProfile(depth=10,
                       durability=DurabilityPolicy.TRANSIENT_LOCAL,
                       reliability=ReliabilityPolicy.RELIABLE))
        
        # Публикация на /tf
        self.tf_pub = self.create_publisher(
            TFMessage, '/tf', 
            QoSProfile(depth=100))
        
        # Публикация на /tf_static
        self.tf_static_pub = self.create_publisher(
            TFMessage, '/tf_static',
            QoSProfile(depth=10,
                      durability=DurabilityPolicy.TRANSIENT_LOCAL))
    
    def tf_callback(self, msg):
        self.tf_pub.publish(msg)
    
    def tf_static_callback(self, msg):
        self.tf_static_pub.publish(msg)
```

**Особенности реализации:**

1. **QoS профили**: подписка на `/robot1/tf` использует BEST_EFFORT
   (трансформации публикуются с высокой частотой, допустима потеря).
   Статические трансформации используют TRANSIENT_LOCAL для гарантии
   доставки всем подписчикам.

2. **Буферизация**: TF relay не буферизирует трансформации — он работает
   как прозрачный прокси. Буферизация выполняется на стороне
   tf2_ros::Buffer в elevation_mapping_node.

3. **Минимальная задержка**: relay работает в том же контейнере, что
   и симулятор, поэтому дополнительная сетевая задержка отсутствует.

### 3.5.3 Статический publisher map → odom

Для привязки карты высот к глобальной системе координат запускается
статический publisher:

```bash
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map odom
```

Это необходимо, так как в симуляции нет отдельного SLAM-модуля,
и координаты `map` и `odom` совпадают. В реальной системе вместо
этого будет использоваться SLAM (например, RTAB-Map или Cartographer).

### 3.5.4 Настройка DDS discovery

Проблема discovery между контейнерами решена следующим образом:

**Единая RMW-реализация:**

Оба контейнера используют `rmw_cyclonedds_cpp`. Это гарантирует,
что они используют одинаковый протокол discovery.

**Единый ROS_DOMAIN_ID:**

Переменная `ROS_DOMAIN_ID=0` задана для обоих контейнеров.
Это обеспечивает видимость нод друг другу.

**Конфигурация Cyclone DDS:**

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="https://cdds.io/config
            https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd">
    <Domain id="0">
        <General>
            <NetworkInterfaceAddress>lo</NetworkInterfaceAddress>
            <AllowMulticast>true</AllowMulticast>
        </General>
        <Discovery>
            <EnableTopicDiscovery>true</EnableTopicDiscovery>
            <DSGracePeriod>
                <MaxHeartbeatResponses>100</MaxHeartbeatResponses>
            </DSGracePeriod>
        </Discovery>
        <Internal>
            <SharedMemory>
                <Enable>false</Enable>
            </SharedMemory>
        </Internal>
    </Domain>
</CycloneDDS>
```

### 3.5.5 Диагностика discovery

Для диагностики проблем discovery используются инструменты:

- `ros2 node list` — проверка видимости нод между контейнерами.
- `ros2 topic list` — проверка доступных топиков.
- `ros2 topic echo /tf` — проверка наличия трансформаций.
- Cyclone DDS трассировка: `CYCLONEDDS_URI=file:///cyclonedds.xml`
  с включённым `<Tracing>`.

Типичные проблемы и их решения:

| Проблема | Причина | Решение |
|----------|---------|---------|
| Ноды не видны | Разные ROS_DOMAIN_ID | Установить единый ID |
| TF не публикуется | Неправильный QoS | Использовать BEST_EFFORT |
| PointCloud не принимается | SHM конфликт | Отключить SHM в Cyclone |
| Discovery медленный | Много интерфейсов | Явно указать lo interface |

### 3.5.6 Оптимизация сетевого трафика

Учитывая, что PointCloud2 на 10 Гц может генерировать значительный
трафик (360×16×4 байт × 10 Гц ≈ 230 КБ/с), дополнительно применяются
оптимизации:

- **Отключение SHM**: гарантирует использование UDP, что стабильнее
  при межконтейнерной передаче.
- **Network interface**: явное указание lo interface предотвращает
  широковещательный discovery на внешние сети.
- **TCP_NODELAY**: Cyclone DDS использует TCP_NODELAY по умолчанию
  для минимизации задержки.

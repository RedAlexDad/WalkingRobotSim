# Конвертация LaserScan → range image

## Задача

Конвертировать `sensor_msgs/LaserScan` (1D массив дальностей) в range image (2D массив) для подачи в SqueezeSegV3.

## Проблема

Наш LiDAR в Gazebo — **однолучевой** (single-layer LaserScan), а SqueezeSegV3 ожидает **многолучевой** (64 канала) range image.

## Решение: псевдо-range image

Создаём range image из последовательных сканов:

```
Range image: H × W
H = количество последовательных сканов (временная ось)
W = количество лучей в одном скане
```

Или альтернатива: используем **Gazebo GPU LiDAR** с multiple rays по вертикали.

## Подход 1: Временной стек (проще)

```python
import numpy as np

class ScanAccumulator:
    def __init__(self, window_size=64):
        self.window_size = window_size
        self.buffer = []

    def add_scan(self, scan_msg):
        ranges = np.array(scan_msg.ranges)
        # Заменяем inf на max_range
        ranges[np.isinf(ranges)] = scan_msg.range_max
        self.buffer.append(ranges)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)

    def get_range_image(self):
        if len(self.buffer) < self.window_size:
            return None
        # H x W: время x горизонтальные лучи
        return np.stack(self.buffer)  # 64 x 1080
```

## Подход 2: Gazebo GPU LiDAR (лучше)

Заменить стандартный LiDAR на GPU LiDAR с вертикальными лучами:

```xml
<sensor name="gpu_lidar" type="gpu_lidar">
  <lidar>
    <scan>
      <horizontal>
        <samples>1024</samples>
        <resolution>1</resolution>
        <min_angle>-3.14</min_angle>
        <max_angle>3.14</max_angle>
      </horizontal>
      <vertical>
        <samples>64</samples>
        <resolution>1</resolution>
        <min_angle>-0.26</min_angle>
        <max_angle>0.26</max_angle>
      </vertical>
    </lidar>
  </lidar>
</sensor>
```

## Конвертация в формат SqueezeSegV3

```python
def convert_to_squeezeseg_format(range_image):
    """
    range_image: H x W (depth values)
    Returns: H x W x 3 (depth, x, y)
    """
    H, W = range_image.shape

    # Углы
    u = np.linspace(-np.pi, np.pi, W)  # горизонтальные
    v = np.linspace(-0.26, 0.26, H)    # вертикальные

    # Сферические → декартовы
    uu, vv = np.meshgrid(u, v)
    x = range_image * np.cos(vv) * np.cos(uu)
    y = range_image * np.cos(vv) * np.sin(uu)

    return np.stack([range_image, x, y], axis=-1)
```

## Связанные заметки

- [[Запись данных]] — предыдущий шаг
- [[Инференс и метрики]] — следующий шаг

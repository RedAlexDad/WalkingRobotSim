# Глава 3. Разработка модуля Elevation Mapping и terrain-aware планирования

## 3.7 Ground segmentation

### 3.7.1 Постановка задачи

Для корректного построения карты высот необходимо разделить облако точек
на два класса:

- **Ground точки**: принадлежат поверхности земли. Используются для
  обновления карты высот (DEM).
- **Non-ground точки**: принадлежат препятствиям, объектам, нависающим
  структурам. Используются для идентификации препятствий и маркировки
  no-go зон.

Задача ground segmentation (сегментации поверхности земли) является
классической проблемой обработки данных LiDAR. Основные сложности:

- Рельеф может быть неровным (холмы, овраги), что делает простой
  пороговый фильтр по z-координате неприменимым.
- Наличие наклонных поверхностей (пандусы, склоны), которые являются
  проходимыми, но не являются строго горизонтальными.
- Шум измерений, создающий ложные ground точки.

### 3.7.2 Алгоритм Ground Plane Fitting (Zermas 2017)

Выбран алгоритм Ground Plane Fitting, описанный в статье
"Fast segmentation of 3D point clouds for ground vehicles"
(Zermas et al., 2017), адаптированный для ROS 2 Jazzy.

Алгоритм состоит из следующих шагов:

**Шаг 1: Подготовка данных**

Входное облако точек преобразуется из формата PointCloud2
в массив numpy (N, 3) с координатами (x, y, z).

**Шаг 2: Фильтрация по высоте**

Отбрасываются точки выше `max_height` и ниже `min_height`
относительно сенсора:
```
if z > sensor_z + max_height or z < sensor_z + min_height:
    filter_out()
```

Параметры:
- `max_height`: 0.5 м (максимальная высота точки над сенсором).
- `min_height`: -0.5 м (максимальная глубина точки под сенсором).

**Шаг 3: Выбор кандидатов для начальной плоскости**

Из отфильтрованного облака выбираются точки с наименьшей
z-координатой (нижние 20%). Это увеличивает вероятность того,
что выбранные точки принадлежат ground, а не препятствиям.

**Шаг 4: Итеративная подгонка плоскости (RANSAC)**

Для каждой из `max_iterations` (3) итераций:

1. Из нижних 20% точек случайно выбираются 3 точки.
2. Через них проводится плоскость: n·x + d = 0.
3. Вычисляется расстояние от каждой точки облака до плоскости:
   `distance = |n·x_i + d| / ||n||`
4. Точки с distance < `distance_threshold_i` считаются inliers (ground).
5. На каждой итерации порог увеличивается:
   - Итерация 1: порог = 0.15 м
   - Итерация 2: порог = 0.25 м
   - Итерация 3: порог = 0.35 м

Увеличение порога на каждой итерации позволяет захватывать
неровный рельеф: первая итерация находит "ядро" плоскости,
последующие — присоединяют точки с отклонениями.

**Шаг 5: Формирование результата**

- Inliers (близкие к плоскости) → ground_cloud.
- Outliers (далёкие от плоскости) → obstacle_cloud.

### 3.7.3 Реализация для ROS 2 Jazzy

Нода `ground_segmenter` из пакета `walkingrobot_vision`:

```python
import rclpy
import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from rclpy.qos import QoSProfile

class GroundSegmenter(Node):
    def __init__(self):
        super().__init__('ground_segmenter')
        
        # Параметры
        self.declare_parameter('max_iterations', 3)
        self.declare_parameter('distance_threshold', 0.2)
        self.declare_parameter('max_height', 0.5)
        self.declare_parameter('min_height', -0.5)
        self.declare_parameter('num_lower_points', 20)  # процентиль
        
        # Подписка
        self.sub = self.create_subscription(
            PointCloud2, '/robot1/scan/points',
            self.cloud_callback, 
            QoSProfile(depth=10))
        
        # Публикация
        self.ground_pub = self.create_publisher(
            PointCloud2, '/ground_cloud', 10)
        self.obstacle_pub = self.create_publisher(
            PointCloud2, '/obstacle_cloud', 10)
    
    def cloud_callback(self, msg):
        # Конвертация PointCloud2 → numpy
        points = self.pointcloud2_to_numpy(msg)
        
        # Фильтрация по высоте
        mask = (points[:, 2] > self.max_height) | \
               (points[:, 2] < self.min_height)
        points = points[~mask]
        
        # Ground Plane Fitting
        ground, obstacles = self.ground_plane_fitting(points)
        
        # Публикация
        if ground.shape[0] > 0:
            self.ground_pub.publish(
                self.numpy_to_pointcloud2(ground, msg.header))
        if obstacles.shape[0] > 0:
            self.obstacle_pub.publish(
                self.numpy_to_pointcloud2(obstacles, msg.header))
```

### 3.7.4 Интеграция с elevation_mapping

Ground-облако подаётся на вход elevation_mapping_node вместо полного
облака точек. Это обеспечивает:

1. **Чистую карту высот**: на карту попадают только точки поверхности
   земли, без влияния препятствий.

2. **Корректную traversability**: non-ground точки маркируются как
   препятствия и учитываются в cost map.

3. **Раздельную частоту обработки**: ground может обновляться на
   каждом кадре (10 Гц), в то время как obstacle map может
   накапливаться за несколько кадров для снижения шума.

### 3.7.5 Альтернативные алгоритмы

Для сравнения рассмотрены следующие альтернативы:

**GPF (Ground Plane Fitting)** — выбранный алгоритм.
- Плюсы: быстрый, простой в реализации, работает на неровном рельефе.
- Минусы: не работает на вертикальных поверхностях (стены).

**RANSAC с одной плоскостью**:
- Плюсы: очень быстрый (1 итерация).
- Минусы: не захватывает неровный рельеф, теряет ground на холмах.

**Ray-based filtering (Patchwork)**:
- Плюсы: сегментирует даже на сложном рельефе.
- Минусы: требует больше ресурсов, сложнее в настройке.

**LineFit (Miltiadis et al.)**:
- Плюсы: эффективен для разреженных облаков.
- Минусы: требует упорядоченного облака (по строкам сканирования).

### 3.7.6 Метрики качества сегментации

Для оценки качества ground segmentation используются метрики:

| Метрика | Описание | Целевое значение |
|---------|----------|-----------------|
| Precision | Доля истинных ground среди предсказанных ground | > 95% |
| Recall | Доля найденных ground точек от всех ground | > 90% |
| F1-score | Гармоническое среднее precision и recall | > 0.92 |
| FP rate | Доля non-ground, ошибочно отнесённых к ground | < 5% |

Для получения ground truth в симуляции Gazebo создаётся дополнительное
облако точек, содержащее только поверхность земли (без препятствий),
и сравнивается с результатом сегментации.

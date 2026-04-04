# Обзор моделей семантической сегментации LiDAR

## Задача

Семантическая сегментация 3D LiDAR данных — присвоение каждому пункту (point) облака метки класса: дорога, здание, дерево, автомобиль, пешеход и т.д.

## Основные подходы

### 1. Point-based методы

Работают напрямую с облаком точек.

| Модель | Год | Архитектура | Плюсы | Минусы |
|--------|-----|-------------|-------|--------|
| **PointNet** | 2017 | MLP на точках | Простая, первая | Не захватывает локальную структуру |
| **PointNet++** | 2017 | Иерархическая | Лучше локальные признаки | Медленная |
| **RandLA-Net** | 2020 | Random sampling + local feature | Быстрая на больших облаках | Требует много памяти |

### 2. Projection-based методы

Проецируют 3D точки на 2D изображение (range image).

| Модель | Год | Архитектура | Плюсы | Минусы |
|--------|-----|-------------|-------|--------|
| **SqueezeSeg** | 2018 | SqueezeNet + CRF | Быстрая, легкая | Потеря 3D структуры |
| **SqueezeSegV2** | 2019 | + Context modules | Лучше точность | Сложнее |
| **SqueezeSegV3** | 2020 | + Spatial-depthwise conv | SOTA среди проекционных | — |
| **RangeNet++** | 2019 | DarkNet-21 + KNN post-processing | Популярная, есть готовые веса | KNN постобработка медленная |

### 3. Voxel-based методы

Дискретизируют пространство в воксели.

| Модель | Год | Архитектура | Плюсы | Минусы |
|--------|-----|-------------|-------|--------|
| **3D MinusNet** | 2018 | 3D sparse conv | Точная | Медленная |
| **MinkowskiNet** | 2019 | Sparse tensor conv | Эффективная | Сложная реализация |
| **Cylinder3D** | 2021 | Cylindrical partitioning | SOTA | Требует GPU |

## Рекомендация для статьи

### Выбор: **RangeNet++** или **SqueezeSegV3**

**Почему:**
- Работают с range images (2D проекция) — легко интегрировать с Gazebo LiDAR
- Есть **готовые предобученные веса** (SemanticKITTI, 19 классов)
- Не требуют обучения с нуля — можно сразу делать инференс
- Легко получить метрики (IoU per class, mIoU)
- Хорошо подходят для демонстрации в статье

### Альтернатива: **RandLA-Net**

- Если хотим показать работу с raw point cloud
- Более «современный» подход
- Но сложнее в интеграции

## Датасеты для предобученных моделей

| Датасет | Классов | Сцена | Ссылка |
|---------|---------|-------|--------|
| **SemanticKITTI** | 19 | Городские дороги | [semantickitti.com](http://www.semantic-kitti.org/) |
| **SemanticPOSS** | 8 | Парковки | [github](https://github.com/PRBonn/semantic-kitti-api) |
| **nuScenes** | 16 | Городские | [nuscenes.org](https://www.nuscenes.org/) |

## Ключевые метрики для статьи

- **mIoU** (mean Intersection over Union) — основная метрика
- **Per-class IoU** — по каждому классу
- **Accuracy** — общая точность
- **Inference time** — время обработки одного скана

## Ссылки

- [RangeNet++ GitHub](https://github.com/PRBonn/rangenet_plus_plus)
- [SqueezeSegV3 GitHub](https://github.com/chenfengxu714/SqueezeSegV3)
- [SemanticKITTI API](https://github.com/PRBonn/semantic-kitti-api)
- [Обзор методов (2023)](https://arxiv.org/abs/2303.02415)

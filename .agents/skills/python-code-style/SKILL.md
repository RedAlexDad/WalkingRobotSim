# Python Code Style

## Общие правила

- **Кодировка**: UTF-8
- **Отступы**: 4 пробела (без табуляции)
- **Максимум строки**: 100 символов (PEP-8 рекомендует 79, но проект использует 100)
- **Импорты**: в алфавитном порядке, разделённые на группы:
  1. Стандартная библиотека
  2. Сторонние библиотеки (numpy, torch, etc.)
  3. Внутренние модули проекта

## Логирование

- **ЗАПРЕЩЕНО** использовать `print()` в production коде
- Использовать `_log.info()`, `_log.warning()`, `_log.error()` из `walking_robot_utils.logging`
- Для ROS2 нод использовать `self.get_logger().info()`
- Для библиотечного кода (не ROS2) добавлять модульный логгер:

```python
try:
    from walking_robot_utils.logging import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging as _logging
    _log = _logging.getLogger(__name__)
    _log.addHandler(_logging.StreamHandler())
    _log.setLevel(_logging.INFO)
```

## Numba

- CPU-оптимизации через `@njit` (без `cache=True` — файловая система может быть read-only)
- Numba-функции должны быть вынесены в отдельные standalone-функции (не методы класса)
- Результат должен быть bit-identical (< 1e-9) с оригинальным алгоритмом

## Типизация

- Обязательно использовать type hints для новых функций
- Принятые типы: `List[T]`, `Dict[K, V]`, `Optional[T]`, `Tuple[T, ...]`, `Union[T1, T2]`

## Производительность

- Избегать `for i in range(len(arr))` — использовать numpy векторизацию
- CPU-циклы > 10K итераций — оборачивать в `@njit`
- Импорты выносить наверх модуля, а не внутрь функций (особенно в hot path)

## Именование

- `snake_case` для функций и переменных
- `PascalCase` для классов
- `UPPER_CASE` для констант
- Односимвольные имена (`i`, `x`, `n`) допустимы только в коротких циклах (≤ 5 строк)

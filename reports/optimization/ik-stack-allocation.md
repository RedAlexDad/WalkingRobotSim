# Report 2026-06-14_014101 MSK

**Branch:** feat/elevation-mapping
**Stats:** 3 files changed, 58 insertions(+), 27 deletions(-)

## Что было изменено
- `inverse_kinematics.hpp/cpp`: все `Eigen::MatrixXd` (heap) заменены на `Eigen::Matrix<double, 4, 3>` (стек), `std::vector<double>` на `std::array<double, 12>` — исключены 2 heap-аллокации на тик control loop
- `inverse_kinematics.cpp`: матрица `R_legs` сделана `static const` — инициализируется один раз
- `benchmark_utils.h`: добавлена перегрузка `print_joints` для `std::array<double, 12>` — совместимость бенчмарков с новыми типами

## Проблемы
- Разрыв совместимости: `benchmark` использовал `print_joints` для `std::vector<double>`, но `inverse_kinematics` теперь возвращает `std::array`. Решено добавлением перегрузки

## Что нужно учитывать в будущем
- `Eigen::Matrix<double, 4, 3>` (стек) не требует `setZero()` — значение-инициализируется нулями по умолчанию
- `std::array<double, 12>` инициализируется `{}` — без лишнего заполнения нулями в отличие от `std::vector<double>(12, 0.0)`
- При изменении возвращаемого типа публичной функции нужно проверять все call site (test, benchmark, node)

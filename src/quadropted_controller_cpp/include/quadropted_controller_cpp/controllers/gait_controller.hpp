/// @file gait_controller.hpp
/// @brief Базовый класс для всех контроллеров походки.
///
/// Определяет общую логику тактирования фаз stance/swing и расчёта контактов.
/// Каждый gait (TROT, CRAWL) наследуется от этого класса и переопределяет step().
///
/// ## Структура цикла походки
///
/// Полный цикл (phase_length) делится на N фаз. Для каждой фазы известен
/// паттерн контактов — какие лапы стоят (1), а какие переносятся (0):
///
/// ```
/// tick:  0 1 2 3 4 5 6 7 8 9 ...
/// фаза:  |---фаза 0---|фаза 1|...
/// FR:    1 1 1 1 0 0 0 0 1 1 ...  (trot: диагонали)
/// FL:    1 1 1 1 0 0 0 0 1 1 ...
/// RR:    0 0 0 0 1 1 1 1 0 0 ...
/// RL:    0 0 0 0 1 1 1 1 0 0 ...
/// ```
///
/// @note В stance лапа неподвижна в мировой системе — корпус движется
///   относительно неё. В swing лапа переносится по траектории Райберта.
///
/// @warning Все потомки ДОЛЖНЫ вызывать compute_phase_ticks() в конструкторе,
///   иначе phase_index() и contacts() будут работать некорректно.
///
/// @see TrotGaitController, CrawlGaitController

#pragma once
#include <Eigen/Dense>
#include <vector>

#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

/// Базовый класс контроллера походки.
///
/// Управляет временем цикла: длительность stance, swing, разбиение на фазы.
/// Предоставляет методы для определения текущей фазы по tick-счётчику.
class GaitController {
  public:
    /// @param stance_time   Длительность фазы опоры [с]
    /// @param swing_time    Длительность фазы переноса [с]
    /// @param time_step     Шаг симуляции [с] (обычно 0.01 = 100 Гц)
    /// @param contact_phases  Матрица контактов: колонки = фазы, строки = лапы.
    ///                        1 — лапа на земле (stance), 0 — перенос (swing).
    ///                        Размер: число_лап × число_фаз.
    /// @param default_stance  Положения лап в покое (3×4). Стоячая поза по умолчанию.
    ///
    /// @note contact_phases определяет порядок перестановки лап.
    ///   Для рыси (trot): [[1,0],[1,0],[0,1],[0,1]] (диагонали FR+RL, FL+RR).
    ///   Для шага (crawl): [[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]].
    GaitController(double stance_time, double swing_time, double time_step, Eigen::MatrixXi contact_phases,
                   Eigen::MatrixXd default_stance);

    /// @return Положения лап в покое (3×4). Константная ссылка — не копируйте.
    const LegsMatrix& default_stance() const { return default_stance_; }

    /// @return Количество тиков в фазе опоры.
    int stance_ticks() const { return stance_ticks_; }

    /// @return Количество тиков в фазе переноса.
    int swing_ticks() const { return swing_ticks_; }

    /// @return Общая длина цикла в тиках (сумма по всем фазам).
    int phase_length() const { return phase_length_; }

    /// @return Вектор кумулятивных длин фаз [тик]. Используется в phase_index().
    const std::vector<int>& phase_ticks() const { return phase_ticks_; }

    /// Определяет индекс текущей фазы (колонку contact_phases_) по счётчику тиков.
    ///
    /// @param ticks  Текущий tick из State::ticks.
    ///
    /// @return Индекс фазы (0 .. число_фаз-1).
    ///
    /// @note Работает через бинарный поиск по phase_ticks_.
    /// @see subphase_ticks(), contacts()
    int phase_index(int ticks) const;

    /// Возвращает номер тика внутри текущей фазы.
    ///
    /// @param ticks  Текущий tick из State::ticks.
    ///
    /// @return Позиция от начала фазы [0 .. длина_фазы-1].
    ///
    /// @note Используется для интерполяции траектории лапы внутри фазы.
    /// @see phase_index()
    int subphase_ticks(int ticks) const;

    /// @brief Возвращает вектор контактов для текущего тика.
    ///
    /// @param ticks  Текущий tick из State::ticks.
    ///
    /// @return Вектор длины 4: 1 = лапа на земле, 0 = лапа в воздухе.
    ///
    /// @warning Размер вектора всегда число_лап (4), НЕ число_фаз.
    /// @see phase_index()
    Eigen::VectorXi contacts(int ticks) const;

  protected:
    double stance_time_;   ///< Время опоры [с]
    double swing_time_;    ///< Время переноса [с]
    double time_step_;     ///< Шаг симуляции [с]

    Eigen::MatrixXi contact_phases_;  ///< Матрица контактов (лапы × фазы)
    LegsMatrix default_stance_;       ///< Положения лап в покое

    int stance_ticks_ = 0;   ///< Тиков в опоре (stance_time_ / time_step_)
    int swing_ticks_ = 0;    ///< Тиков в переносе (swing_time_ / time_step_)
    int phase_length_ = 0;   ///< Суммарная длина цикла в тиках
    std::vector<int> phase_ticks_;  ///< Кумулятивные длины фаз

    /// Вычисляет phase_ticks_, phase_length_, stance_ticks_, swing_ticks_.
    ///
    /// @pre contact_phases_ должна быть инициализирована.
    /// @post phase_ticks_ содержит кумулятивные длины фаз.
    ///
    /// @warning ДОЛЖЕН вызываться в конструкторе потомка.
    void compute_phase_ticks();
};

}  // namespace quadropted

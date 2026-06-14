/// @file state_command.hpp
/// @brief Типы состояний и команд для всех контроллеров походки.
///
/// Определяет базовые структуры данных, которые передаются между компонентами
/// системы управления: состояние робота (положение лап, IMU, tick) и команда
/// управления (целевая скорость, высота, запрос смены режима).
///
/// @note Все высоты задаются относительно "нулевой" позиции ног.
///   Положительное значение = корпус выше, отрицательное = корпус ниже.
/// @see GaitController, RobotControllerNode

#pragma once
#include <Eigen/Dense>
#include <array>

namespace quadropted {

/// Матрица 3×4: [x, y, z] × 4 лапы (FR, FL, RR, RL).
///
/// Строки: 0 — x (вперёд), 1 — y (вбок), 2 — z (вверх).
/// Столбцы: 0 — передняя правая (FR), 1 — передняя левая (FL),
///          2 — задняя правая (RR), 3 — задняя левая (RL).
///
/// @note Это основной тип для передачи положений лап между IK, FK и контроллерами.
///   Размерность 3×4 выбрана для эффективных векторных операций с Eigen.
using LegsMatrix = Eigen::Matrix<double, 3, 4>;

/// Режимы поведения (конечный автомат).
///
/// @warning Порядок важен: используется для switch/case в RobotControllerNode.
///   НЕ меняйте числовые значения без синхронизации с узлом.
enum class BehaviorState {
    REST = 0,  ///< Покой — все лапы на земле, минимальное энергопотребление
    TROT,      ///< Рысь — диагональные пары, максимальная скорость
    CRAWL,     ///< Шаг — одна лапа за раз, максимальная устойчивость
    STAND      ///< Стояние — поза с возможностью наклона корпуса
};

/// Полное состояние робота на текущем тике.
///
/// Содержит всё, что нужно для расчёта следующего положения лап:
///   - текущие положения лап (foot_locations)
///   - показания IMU (roll, pitch)
///   - tick счётчик для фазы походки
///   - текущий режим поведения
///
/// @note Поле robot_height дублирует body_height с обратным знаком.
///   Это исторически сложилось из Python-прототипа StateCommand.py.
/// @warning IMU-данные (imu_roll, imu_pitch) должны обновляться ДО вызова step().
/// @see Command, GaitController::step()
struct State {
    /// Высота корпуса над лапами [м]. Положительная = выше.
    double body_height = 0.25;

    /// Текущие положения лап (3×4) в системе корпуса.
    /// @see LegsMatrix
    LegsMatrix foot_locations;

    /// Смещение корпуса относительно центра [dx, dy, dz] [м].
    /// Используется в StandController для наклонов по команде.
    std::array<double, 3> body_local_position{0, 0, 0};

    /// Ориентация корпуса [roll, pitch, yaw] [рад].
    /// @warning yaw пока не используется — зарезервировано.
    std::array<double, 3> body_local_orientation{0, 0, 0};

    double imu_roll = 0;   ///< Крен с IMU [рад]. Обновляется в callback.
    double imu_pitch = 0;  ///< Тангаж с IMU [рад]. Обновляется в callback.

    /// Tick счётчик (0 .. phase_length-1).
    /// Инкрементируется в control_loop. Используется gait->step().
    /// @see GaitController::phase_index(), GaitController::subphase_ticks()
    int ticks = 0;

    /// Текущий режим FSM.
    /// @see BehaviorState
    BehaviorState behavior_state = BehaviorState::REST;

    /// Эффективная высота [м]. Обычно отрицательная (корпус ниже опор).
    /// Дублирует body_height с обратным знаком для обратной совместимости.
    /// @note При смене режима пересчитывается в change_controller().
    double robot_height = -0.25;

    State() = default;

    /// @param height  Целевая высота корпуса [м] (положительная = выше).
    explicit State(double height) : body_height(height), robot_height(-height) {}
};

/// Высокоуровневая команда управления от телеоперации или автономии.
///
/// Поступает из топика /cmd_vel (через cmd_vel_pub) или /robot_velocity.
/// Содержит целевые скорости и флаги для переключения режимов.
///
/// @note Флаги trot_event/rest_event по умолчанию true, чтобы при старте
///   робот сразу перешёл в один из режимов. Это поведение можно изменить
///   через параметры в YAML.
/// @warning Одновременно должен быть установлен только один флаг события.
///   Если установлены несколько — приоритет: STAND > CRAWL > TROT > REST.
/// @see State, RobotControllerNode::control_loop()
struct Command {
    /// Целевая линейная скорость [vx, vy, vz] [м/с].
    /// vx — вперёд, vy — вбок, vz — вверх (обычно 0 для gait).
    std::array<double, 3> velocity{0, 0, 0};

    /// Целевая угловая скорость [ax, ay, az] [рад/с].
    /// az — рысканье (поворот), ax/ay — обычно 0.
    std::array<double, 3> yaw_rate{0, 0, 0};

    /// Целевая высота корпуса [м]. Отрицательная = ниже.
    /// @note Не путать с body_height в State: robot_height имеет обратный знак.
    double robot_height = -0.25;

    /// Флаг запроса перехода в режим TROT.
    /// @warning После обработки сбрасывается в change_controller().
    bool trot_event = true;

    /// Флаг запроса перехода в режим REST.
    bool rest_event = true;

    bool crawl_event = false;  ///< Флаг запроса перехода в режим CRAWL
    bool stand_event = false;  ///< Флаг запроса перехода в режим STAND
};

}  // namespace quadropted

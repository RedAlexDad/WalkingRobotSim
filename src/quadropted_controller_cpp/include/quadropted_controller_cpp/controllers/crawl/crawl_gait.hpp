/// @file crawl_gait.hpp
/// @brief Контроллер походки «шаг» (crawl) — одна лапа за раз.
///
/// Crawl — самая медленная, но самая устойчивая походка. Лапы переставляются
/// по одной: FR → RR → FL → RL. В каждый момент три лапы на земле.
///
/// ## Особенности
/// - Максимальная статическая устойчивость (3 точки опоры)
/// - Боковое смещение корпуса (body_shift_y) для переноса веса
/// - Первый цикл отличается — инициализация фаз
///
/// ## Применение
/// Используется при движении по пересечённой местности или когда
/// требуется максимальная устойчивость (например, перенос груза).
///
/// @warning Сброс (reset()) необходим при повторном включении, иначе
///   first_cycle_ останется false и фазы собьются.
///
/// @see GaitController, CrawlStanceController, CrawlSwingController

#pragma once
#include "quadropted_controller_cpp/controllers/crawl/crawl_stance.hpp"
#include "quadropted_controller_cpp/controllers/crawl/crawl_swing.hpp"
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"

namespace quadropted {

/// Контроллер шагающей походки (одна лапа за раз).
class CrawlGaitController : public GaitController {
  public:
    /// @param stance_time     Длительность опоры [с]
    /// @param swing_time      Длительность переноса [с]
    /// @param time_step       Шаг симуляции [с]
    /// @param default_stance  Положения лап в покое (3×4)
    /// @param z_leg_lift      Высота подъёма лапы [м] (по умолчанию 0.14)
    /// @param body_shift_y    Смещение корпуса вбок для переноса веса [м] (0.06)
    /// @param z_error_constant Коэффициент коррекции высоты (0.02)
    CrawlGaitController(double stance_time, double swing_time, double time_step, Eigen::MatrixXd default_stance,
                        double z_leg_lift = 0.14, double body_shift_y = 0.06,
                        double z_error_constant = 0.02);

    /// Выполнить шаг походки.
    ///
    /// @param ticks       Текущий tick счётчика
    /// @param current     Текущие положения лап (3×4)
    /// @param cmd_vel     Целевая скорость [vx, vy, vz]
    /// @param robot_height Целевая высота корпуса [м]
    ///
    /// @return Новые положения лап (3×4)
    ///
    /// @note Если first_cycle_, первые несколько тиков инициализируют
    ///   фазы без движения — это предотвращает рывок при старте.
    LegsMatrix step(int ticks, const LegsMatrix& current, const Eigen::Vector3d& cmd_vel, double robot_height);

    /// Сброс состояния к первому циклу.
    void reset();
    CrawlSwingController& swing() { return swing_; }
    CrawlStanceController& stance() { return stance_; }
    bool is_first_cycle() const { return first_cycle_; }

  private:
    CrawlSwingController swing_;  ///< Контроллер фазы переноса
    CrawlStanceController stance_;  ///< Контроллер фазы опоры
    bool first_cycle_ = true;       ///< Флаг первого цикла после создания/reset
};

}  // namespace quadropted

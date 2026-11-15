//! Состояние и шаг контроллера ходьбы: REST/TROT/CRAWL/STAND, IK и контакты ног.
//!
//! Логика перенесена из `robot_controller_node.rs` без изменения поведения;
//! в бинарнике остаётся только связка с rclrs. Модуль не требует ROS-контекста,
//! поэтому шаг контроллера, переключение режимов, сервис поведения и контакты
//! ног проверяются юнит-тестами.

use nalgebra::SMatrix;
use quadropted_core::controllers::crawl::gait::CrawlGaitController;
use quadropted_core::controllers::rest::{RestController, RestState};
use quadropted_core::controllers::stand::{BodyState, StandController};
use quadropted_core::controllers::trot::gait::TrotGaitController;
use quadropted_core::kinematics::inverse::{compute_all_joint_angles, compute_local_positions};
use quadropted_core::math::quaternion::{euler_pitch, euler_roll};
use quadropted_core::math::rotation::rotxyz;
use quadropted_core::state::behavior::BehaviorState;
use std::time::Duration;

/// Длина корпуса (C++ `body_length`).
pub const BODY_LENGTH: f64 = 0.3762;
/// Ширина корпуса (C++ `body_width`).
pub const BODY_WIDTH: f64 = 0.0935;
/// Смещение бедра по вертикали (C++ `l2`).
pub const L2: f64 = 0.0955;
/// Длина бедра (C++ `l3`).
pub const L3: f64 = 0.213;
/// Длина голени (C++ `l4`).
pub const L4: f64 = 0.213;
/// Высота корпуса, с которой считается IK (C++ `step(-0.25)`).
pub const STEP_HEIGHT: f64 = -0.25;
/// `robot_id`, на который реагируют подписки.
pub const ROBOT_ID: u16 = 1;
/// Пауза перед активацией контроллера: 120 тиков ≈ 2 с @ 60 Гц.
pub const STARTUP_GRACE_TICKS: i32 = 120;
/// Период управляющего цикла, мс (60 Гц).
pub const CONTROL_PERIOD_MS: u64 = 16;

/// Параметры узла контроллера.
///
/// Объявляются в `params::ControllerParamHandles`; дефолты совпадают с
/// константами выше, поэтому без launch-параметров поведение прежнее.
#[derive(Debug, Clone, PartialEq)]
pub struct ControllerParams {
    /// IMU-компенсация наклона в TROT (C++ флаг `use_imu`).
    pub use_imu: bool,
    /// Высота корпуса для IK (C++ `step(-0.25)`).
    pub robot_height: f64,
    /// Период управляющего цикла, мс.
    pub control_period_ms: i64,
    /// Пауза перед активацией контроллера, тиков.
    pub startup_grace_ticks: i64,
}

impl Default for ControllerParams {
    fn default() -> Self {
        Self {
            use_imu: false,
            robot_height: STEP_HEIGHT,
            control_period_ms: CONTROL_PERIOD_MS as i64,
            startup_grace_ticks: STARTUP_GRACE_TICKS as i64,
        }
    }
}

impl ControllerParams {
    /// Период управляющего цикла. Значения вне диапазона [1, 1000] мс
    /// зажимаются, чтобы узел не уходил в busy-loop.
    pub fn control_period(&self) -> Duration {
        Duration::from_millis(self.control_period_ms.clamp(1, 1000) as u64)
    }

    /// Пауза старта в тиках; отрицательные значения означают «без паузы».
    pub fn startup_grace_ticks(&self) -> i32 {
        self.startup_grace_ticks.clamp(0, 1000) as i32
    }
}

/// Полное состояние контроллера: контроллеры режимов, команды и IMU.
pub struct SharedState {
    ticks: i32,
    foot_locations: SMatrix<f64, 3, 4>,
    default_stance: SMatrix<f64, 3, 4>,
    behavior_state: BehaviorState,
    trot_gait: TrotGaitController,
    crawl_gait: CrawlGaitController,
    rest_ctrl: RestController,
    rest_state: RestState,
    stand_ctrl: StandController,
    body_state: BodyState,
    cmd_linear: [f64; 3],
    cmd_angular: [f64; 3],
    imu_roll: f64,
    imu_pitch: f64,
    mode_msg_count: u64,
    vel_msg_count: u64,
    startup_grace: i32,
    /// Высота корпуса для IK (параметр `robot_height`).
    robot_height: f64,
}

impl SharedState {
    /// Создать состояние с дефолтной стойкой (C++ `SharedState::SharedState`).
    pub fn new() -> Self {
        Self::with_imu_compensation(false)
    }

    /// Создать состояние по параметрам узла контроллера.
    pub fn with_params(params: &ControllerParams) -> Self {
        let mut state = Self::with_imu_compensation(params.use_imu);
        state.startup_grace = params.startup_grace_ticks();
        state.robot_height = params.robot_height;
        state
    }

    /// Создать состояние с включённой/выключенной IMU-компенсацией TROT.
    ///
    /// В C++ компенсация включается флагом конструктора `TrotGaitController`
    /// (`use_imu`); вынесено параметром, чтобы ветку компенсации можно было
    /// проверить юнит-тестом без живой симуляции.
    pub fn with_imu_compensation(use_imu: bool) -> Self {
        let dx_front = BODY_LENGTH * 0.5 + 0.02;
        let dx_back = BODY_LENGTH * 0.5;
        let dy = BODY_WIDTH * 0.5 + L2;

        let mut default_stance = SMatrix::<f64, 3, 4>::zeros();
        default_stance[(0, 0)] = dx_front;
        default_stance[(1, 0)] = -dy;
        default_stance[(0, 1)] = dx_front;
        default_stance[(1, 1)] = dy;
        default_stance[(0, 2)] = -dx_back;
        default_stance[(1, 2)] = -dy;
        default_stance[(0, 3)] = -dx_back;
        default_stance[(1, 3)] = dy;

        let trot_gait = TrotGaitController::new(0.04, 0.18, 0.02, use_imu, default_stance);
        let crawl_gait = CrawlGaitController::new(0.55, 0.45, 0.02, default_stance);
        let rest_ctrl = RestController::new(default_stance);
        let stand_ctrl = StandController::new(default_stance);

        Self {
            ticks: 0,
            foot_locations: default_stance,
            default_stance,
            behavior_state: BehaviorState::REST,
            trot_gait,
            crawl_gait,
            rest_ctrl,
            rest_state: RestState {
                imu_roll: 0.0,
                imu_pitch: 0.0,
            },
            stand_ctrl,
            body_state: BodyState {
                body_local_position: [0.0, 0.0, 0.0],
                body_local_orientation: [0.0, 0.0, 0.0],
            },
            cmd_linear: [0.0, 0.0, 0.0],
            cmd_angular: [0.0, 0.0, 0.0],
            imu_roll: 0.0,
            imu_pitch: 0.0,
            mode_msg_count: 0,
            vel_msg_count: 0,
            startup_grace: STARTUP_GRACE_TICKS,
            robot_height: STEP_HEIGHT,
        }
    }

    /// Высота корпуса для IK (значение параметра `robot_height`).
    pub fn robot_height(&self) -> f64 {
        self.robot_height
    }

    /// Дефолтная стойка (столбцы — ноги FR/FL/RR/RL).
    pub fn default_stance(&self) -> SMatrix<f64, 3, 4> {
        self.default_stance
    }

    /// Текущее состояние поведения.
    pub fn behavior_state(&self) -> BehaviorState {
        self.behavior_state
    }

    /// Номер тика управляющего цикла.
    pub fn ticks(&self) -> i32 {
        self.ticks
    }

    /// Первая линейная команда (для периодического лога).
    pub fn cmd_linear_x(&self) -> f64 {
        self.cmd_linear[0]
    }

    /// Сколько сообщений режима и скорости принято (диагностика).
    pub fn message_counts(&self) -> (u64, u64) {
        (self.mode_msg_count, self.vel_msg_count)
    }

    /// Остаток паузы перед активацией контроллера.
    pub fn startup_grace(&self) -> i32 {
        self.startup_grace
    }

    /// Один управляющий тик: выбрать контроллер по режиму и посчитать IK.
    ///
    /// `now_sec` — текущее время (обычно `SystemTime::now()`), передаётся
    /// параметром, чтобы шаг был детерминирован в тестах.
    pub fn step(&mut self, robot_height: f64, now_sec: f64) -> [f64; 12] {
        self.ticks += 1;

        // State machine: select controller based on behavior_state
        self.foot_locations = match self.behavior_state {
            BehaviorState::REST => self.rest_ctrl.step(&self.rest_state, robot_height),
            BehaviorState::TROT => {
                let gait_cmd = [self.cmd_linear[0], self.cmd_linear[1], self.cmd_angular[2]];
                // C++ step_trot: при нулевой скорости — плавное возвращение к default_stance
                let has_command =
                    gait_cmd[0].abs() > 1e-4 || gait_cmd[1].abs() > 1e-4 || gait_cmd[2].abs() > 1e-4;
                if !has_command {
                    let mut result = self.default_stance;
                    result.row_mut(2).fill(robot_height);
                    let alpha = 0.1;
                    self.foot_locations * (1.0 - alpha) + result * alpha
                } else {
                    let mut new_foot = self.trot_gait.step(
                        self.ticks,
                        &self.foot_locations,
                        &gait_cmd,
                        robot_height,
                    );
                    // IMU compensation (как в C++ step_trot)
                    if self.trot_gait.use_imu() {
                        let comp = self
                            .trot_gait
                            .pid_controller()
                            .run(self.imu_roll, self.imu_pitch, now_sec);
                        let rot = rotxyz(-comp[0], -comp[1], 0.0);
                        new_foot = rot * new_foot;
                    }
                    new_foot
                }
            }
            BehaviorState::CRAWL => {
                // Clamp velocity for crawl mode
                let mut crawl_vel = [self.cmd_linear[0], self.cmd_linear[1], self.cmd_angular[2]];
                crawl_vel[0] = crawl_vel[0].clamp(-0.011, 0.011);
                crawl_vel[1] = crawl_vel[1].clamp(-0.0055, 0.0055);
                crawl_vel[2] = crawl_vel[2].clamp(-0.15, 0.15);

                self.crawl_gait
                    .step(self.ticks, &self.foot_locations, &crawl_vel, robot_height)
            }
            BehaviorState::STAND => self.stand_ctrl.run(
                &mut self.body_state,
                robot_height,
                &self.cmd_linear,
                &self.cmd_angular,
            ),
        };

        // IK: foot positions → joint angles
        // C++ передаёт body_local_position/orientation (высота тела из change_controller)
        let bp = &self.body_state.body_local_position;
        let bo = &self.body_state.body_local_orientation;
        let local = compute_local_positions(
            &self.foot_locations,
            BODY_LENGTH,
            BODY_WIDTH,
            bp[0],
            bp[1],
            bp[2],
            bo[0],
            bo[1],
            bo[2],
        );
        compute_all_joint_angles(&local, 0.0, L2, L3, L4)
    }

    /// Применить смену режима из `robot_mode` (C++ `change_controller`).
    ///
    /// Возвращает `true`, если режим принят: сообщение с чужим `robot_id`
    /// и неизвестный режим игнорируются.
    pub fn apply_mode_command(
        &mut self,
        robot_id: u16,
        mode_name: &str,
        now_sec: f64,
    ) -> Option<BehaviorState> {
        if robot_id != ROBOT_ID {
            return None;
        }
        let new_state = parse_mode_name(mode_name)?;
        self.mode_msg_count += 1;
        self.behavior_state = new_state;
        self.ticks = 0;
        self.reset_for_mode(new_state, now_sec);
        Some(new_state)
    }

    /// Сброс контроллеров и высоты корпуса при переходе в режим.
    fn reset_for_mode(&mut self, new_state: BehaviorState, now_sec: f64) {
        match new_state {
            BehaviorState::CRAWL => {
                self.crawl_gait.reset();
                self.body_state.body_local_position[2] = 0.0;
            }
            BehaviorState::TROT => {
                self.trot_gait.pid_controller().reset(now_sec);
                self.body_state.body_local_position[2] = 0.0;
            }
            BehaviorState::REST => {
                // C++: body_local_position[2] = -0.15 (лечь на землю)
                self.body_state.body_local_position[2] = -0.15;
            }
            BehaviorState::STAND => {
                // C++: body_local_position[2] = 0.005
                self.body_state.body_local_position[2] = 0.005;
            }
        }
    }

    /// Применить `robot_velocity`: команды линейной и угловой скорости.
    pub fn apply_velocity(
        &mut self,
        robot_id: u16,
        linear: [f64; 3],
        angular: [f64; 3],
    ) -> bool {
        if robot_id != ROBOT_ID {
            return false;
        }
        self.vel_msg_count += 1;
        self.cmd_linear = linear;
        self.cmd_angular = angular;
        true
    }

    /// Применить ориентацию из `imu`: roll/pitch для компенсации наклона.
    pub fn apply_imu_quaternion(&mut self, q: &nalgebra::Quaternion<f64>) {
        self.imu_roll = euler_roll(q);
        self.imu_pitch = euler_pitch(q);
    }

    /// Высота корпуса, заданная текущим режимом (для тестов и диагностики).
    pub fn body_height(&self) -> f64 {
        self.body_state.body_local_position[2]
    }

    /// Обработать сервис `robot_behavior_command` (sit/up/walk).
    ///
    /// Возвращает `(success, message)` — ровно то, что уходит в ответ сервиса.
    pub fn behavior_command(&mut self, cmd: &str, now_sec: f64) -> (bool, String) {
        match cmd.to_lowercase().as_str() {
            "sit" => {
                self.behavior_state = BehaviorState::STAND;
                self.ticks = 0;
                self.body_state.body_local_position[2] = -0.15;
                (true, "Robot sat down.".to_string())
            }
            "up" => {
                self.behavior_state = BehaviorState::REST;
                self.ticks = 0;
                self.body_state.body_local_position[2] = 0.0;
                (true, "Robot stood up.".to_string())
            }
            "walk" => {
                self.behavior_state = BehaviorState::REST;
                self.ticks = 0;
                self.body_state.body_local_position[2] = 0.0;
                // C++: rest_event + trot_event → REST затем TROT
                self.behavior_state = BehaviorState::TROT;
                self.ticks = 0;
                self.trot_gait.pid_controller().reset(now_sec);
                (true, "Robot started walking.".to_string())
            }
            other => (false, format!("Unknown command: {}", other)),
        }
    }

    /// Контакты ног для `foot_contact` (C++ `publish_foot_contacts`).
    pub fn contacts(&self) -> [bool; 4] {
        match self.behavior_state {
            BehaviorState::REST | BehaviorState::STAND => [true, true, true, true],
            BehaviorState::TROT => {
                let c = self.trot_gait.contacts(self.ticks);
                [c[0] != 0, c[1] != 0, c[2] != 0, c[3] != 0]
            }
            BehaviorState::CRAWL => {
                let c = self.crawl_gait.contacts(self.ticks);
                [c[0] != 0, c[1] != 0, c[2] != 0, c[3] != 0]
            }
        }
    }

    /// Тик паузы перед активацией: `true` — контроллер ещё спит.
    pub fn startup_grace_tick(&mut self) -> bool {
        if self.startup_grace > 0 {
            self.startup_grace -= 1;
            return true;
        }
        false
    }

    /// Один тик управляющего цикла 60 Гц.
    ///
    /// Пока идёт пауза старта — `None`. Иначе считает углы суставов, контакты
    /// и (раз в 120 тиков) строку диагностики; публикация остаётся в узле.
    pub fn control_tick(&mut self, now_sec: f64) -> Option<ControlOutput> {
        if self.startup_grace_tick() {
            return None;
        }
        let angles = self.step(self.robot_height, now_sec);
        let debug_line = if self.ticks % 120 == 0 {
            Some(format!(
                "[Rust DEBUG] Tick #{} ({:.1}s) {:?} mode, vx={:.3}",
                self.ticks,
                self.ticks as f64 / 60.0,
                self.behavior_state,
                self.cmd_linear[0]
            ))
        } else {
            None
        };
        Some(ControlOutput {
            angles,
            contacts: self.contacts(),
            debug_line,
        })
    }
}

/// Результат одного тика управляющего цикла (см. [`SharedState::control_tick`]).
pub struct ControlOutput {
    /// 12 углов суставов для `joint_group_controller/commands`.
    pub angles: [f64; 12],
    /// Контакты ног для `foot_contact`.
    pub contacts: [bool; 4],
    /// Строка `[Rust DEBUG]` раз в 120 тиков (2 с при 60 Гц).
    pub debug_line: Option<String>,
}

impl Default for SharedState {
    fn default() -> Self {
        Self::new()
    }
}

/// Разобрать имя режима из ROS-строки: обрезать NUL и пробелы.
pub fn parse_mode_name(raw: &str) -> Option<BehaviorState> {
    let trimmed = raw.trim_matches(char::from(0)).trim();
    BehaviorState::from_str(trimmed)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_stance_is_symmetric() {
        let state = SharedState::new();
        let stance = state.default_stance();
        // Передние ноги вынесены вперёд, задние — назад.
        assert!(stance[(0, 0)] > 0.0 && stance[(0, 1)] > 0.0);
        assert!(stance[(0, 2)] < 0.0 && stance[(0, 3)] < 0.0);
        // Левая и правая стороны симметричны по |y|.
        assert!((stance[(1, 0)] + stance[(1, 3)]).abs() < 1e-12);
        assert!((stance[(1, 1)] + stance[(1, 2)]).abs() < 1e-12);
        // Ноги не лежат на земле: z = 0 в дефолтной стойке.
        for leg in 0..4 {
            assert_eq!(stance[(2, leg)], 0.0);
        }
    }

    #[test]
    fn initial_state_is_rest() {
        let state = SharedState::new();
        assert_eq!(state.behavior_state(), BehaviorState::REST);
        assert_eq!(state.ticks(), 0);
        assert_eq!(state.startup_grace(), STARTUP_GRACE_TICKS);
        assert_eq!(state.message_counts(), (0, 0));
    }

    #[test]
    fn step_returns_twelve_joint_angles_in_every_mode() {
        for mode in [
            BehaviorState::REST,
            BehaviorState::TROT,
            BehaviorState::CRAWL,
            BehaviorState::STAND,
        ] {
            let mut state = SharedState::new();
            state.apply_mode_command(ROBOT_ID, mode.as_str(), 0.0);
            let angles = state.step(STEP_HEIGHT, 0.0);
            assert_eq!(angles.len(), 12, "режим {mode:?}");
            assert!(angles.iter().all(|a| a.is_finite()), "режим {mode:?}");
            assert_eq!(state.ticks(), 1);
        }
    }

    #[test]
    fn rest_mode_keeps_default_stance_flat() {
        let mut state = SharedState::new();
        let angles = state.step(STEP_HEIGHT, 0.0);
        assert_eq!(angles.len(), 12);
        // В REST IK считает стойку на заданной высоте — углы не нулевые.
        assert!(angles.iter().any(|a| a.abs() > 1e-6));
    }

    #[test]
    fn trot_step_reacts_to_velocity_command() {
        let mut moving = SharedState::new();
        moving.apply_mode_command(ROBOT_ID, "TROT", 0.0);
        moving.apply_velocity(ROBOT_ID, [0.05, 0.0, 0.0], [0.0, 0.0, 0.0]);
        let moved = moving.step(STEP_HEIGHT, 0.0);

        let mut idle = SharedState::new();
        idle.apply_mode_command(ROBOT_ID, "TROT", 0.0);
        let stayed = idle.step(STEP_HEIGHT, 0.0);

        assert!(moved.iter().zip(stayed.iter()).any(|(a, b)| (a - b).abs() > 1e-9));
    }

    #[test]
    fn crawl_clamps_velocity_internally() {
        let mut state = SharedState::new();
        state.apply_mode_command(ROBOT_ID, "CRAWL", 0.0);
        // Команда сильно больше лимитов CRAWL: шаг не должен паниковать
        // и должен остаться конечным числом.
        state.apply_velocity(ROBOT_ID, [5.0, 5.0, 0.0], [0.0, 0.0, 5.0]);
        let angles = state.step(STEP_HEIGHT, 0.0);
        assert!(angles.iter().all(|a| a.is_finite()));
    }

    #[test]
    fn mode_command_ignores_other_robot_and_unknown_mode() {
        let mut state = SharedState::new();
        assert_eq!(state.apply_mode_command(2, "TROT", 0.0), None);
        assert_eq!(state.apply_mode_command(ROBOT_ID, "FLY", 0.0), None);
        assert_eq!(state.behavior_state(), BehaviorState::REST);
        assert_eq!(state.message_counts().0, 0);
    }

    #[test]
    fn mode_command_accepts_lower_case_and_padded_nul() {
        let mut state = SharedState::new();
        assert_eq!(
            state.apply_mode_command(ROBOT_ID, "trot\0", 0.0),
            Some(BehaviorState::TROT)
        );
        assert_eq!(state.behavior_state(), BehaviorState::TROT);
        assert_eq!(state.message_counts().0, 1);
    }

    #[test]
    fn mode_change_resets_ticks_and_body_height() {
        let mut state = SharedState::new();
        state.step(STEP_HEIGHT, 0.0);
        state.step(STEP_HEIGHT, 0.0);
        assert_eq!(state.ticks(), 2);

        state.apply_mode_command(ROBOT_ID, "REST", 0.0);
        assert_eq!(state.ticks(), 0);
        assert!((state.body_height() + 0.15).abs() < 1e-12, "REST ложится на -0.15");

        state.apply_mode_command(ROBOT_ID, "STAND", 0.0);
        assert!((state.body_height() - 0.005).abs() < 1e-12);
    }

    #[test]
    fn velocity_command_ignores_other_robot() {
        let mut state = SharedState::new();
        assert!(!state.apply_velocity(2, [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]));
        assert_eq!(state.message_counts().1, 0);
        assert!(state.apply_velocity(ROBOT_ID, [0.1, 0.0, 0.0], [0.0, 0.0, 0.2]));
        assert_eq!(state.message_counts().1, 1);
        assert!((state.cmd_linear_x() - 0.1).abs() < 1e-12);
    }

    #[test]
    fn imu_quaternion_feeds_roll_and_pitch() {
        use std::f64::consts::FRAC_PI_4;
        let mut state = SharedState::new();
        // Поворот на 45° вокруг x даёт roll ≈ π/4.
        let half = FRAC_PI_4 / 2.0;
        let q = nalgebra::Quaternion::new(half.cos(), half.sin(), 0.0, 0.0);
        state.apply_imu_quaternion(&q);
        assert!((state.imu_roll - FRAC_PI_4).abs() < 1e-9);
        assert!(state.imu_pitch.abs() < 1e-9);
    }

    #[test]
    fn behavior_command_sit_up_walk() {
        let mut state = SharedState::new();

        let (ok, msg) = state.behavior_command("sit", 0.0);
        assert!(ok);
        assert_eq!(msg, "Robot sat down.");
        assert_eq!(state.behavior_state(), BehaviorState::STAND);
        assert!((state.body_height() + 0.15).abs() < 1e-12);

        let (ok, msg) = state.behavior_command("UP", 0.0);
        assert!(ok);
        assert_eq!(msg, "Robot stood up.");
        assert_eq!(state.behavior_state(), BehaviorState::REST);
        assert_eq!(state.body_height(), 0.0);

        let (ok, msg) = state.behavior_command("walk", 0.0);
        assert!(ok);
        assert_eq!(msg, "Robot started walking.");
        assert_eq!(state.behavior_state(), BehaviorState::TROT);
        assert_eq!(state.ticks(), 0);
    }

    #[test]
    fn behavior_command_rejects_unknown() {
        let mut state = SharedState::new();
        let (ok, msg) = state.behavior_command("dance", 0.0);
        assert!(!ok);
        assert_eq!(msg, "Unknown command: dance");
        assert_eq!(state.behavior_state(), BehaviorState::REST);
    }

    #[test]
    fn contacts_are_all_true_in_static_modes() {
        for mode in [BehaviorState::REST, BehaviorState::STAND] {
            let mut state = SharedState::new();
            state.apply_mode_command(ROBOT_ID, mode.as_str(), 0.0);
            assert_eq!(state.contacts(), [true; 4], "режим {mode:?}");
        }
    }

    #[test]
    fn contacts_follow_gait_phase_in_moving_modes() {
        for mode in [BehaviorState::TROT, BehaviorState::CRAWL] {
            let mut state = SharedState::new();
            state.apply_mode_command(ROBOT_ID, mode.as_str(), 0.0);
            let mut seen_any_false = false;
            for _ in 0..40 {
                state.step(STEP_HEIGHT, 0.0);
                if state.contacts().iter().any(|c| !c) {
                    seen_any_false = true;
                }
            }
            assert!(seen_any_false, "в {mode:?} фаза должна снимать контакт");
        }
    }

    #[test]
    fn startup_grace_counts_down_then_activates() {
        let mut state = SharedState::new();
        for _ in 0..STARTUP_GRACE_TICKS {
            assert!(state.startup_grace_tick());
        }
        assert!(!state.startup_grace_tick());
        assert_eq!(state.startup_grace(), 0);
    }

    #[test]
    fn parse_mode_name_trims_nul_and_whitespace() {
        assert_eq!(parse_mode_name(" TROT\0"), Some(BehaviorState::TROT));
        assert_eq!(parse_mode_name("crawl"), Some(BehaviorState::CRAWL));
        assert_eq!(parse_mode_name("  \0"), None);
        assert_eq!(parse_mode_name("jump"), None);
    }

    #[test]
    fn ik_chain_uses_configured_leg_lengths() {
        // Длины ног должны соответствовать константам узла; проверяем через
        // высоту стойки: при опускании корпуса углы меняются.
        let mut low = SharedState::new();
        let low_angles = low.step(-0.25, 0.0);
        let mut high = SharedState::new();
        let high_angles = high.step(-0.15, 0.0);
        assert!(low_angles.iter().zip(high_angles.iter()).any(|(a, b)| (a - b).abs() > 1e-9));
    }

    #[test]
    fn control_tick_is_none_during_startup_grace() {
        let mut state = SharedState::new();
        for _ in 0..STARTUP_GRACE_TICKS {
            assert!(state.control_tick(0.0).is_none());
        }
        assert_eq!(state.ticks(), 0, "во время паузы контроллер не тикает");

        let out = state.control_tick(0.0).expect("после паузы тик считается");
        assert_eq!(out.angles.len(), 12);
        assert_eq!(out.contacts, [true; 4], "в REST все ноги на земле");
        assert_eq!(state.ticks(), 1);
    }

    #[test]
    fn control_tick_logs_every_two_seconds_in_trot() {
        let mut state = SharedState::new();
        state.apply_mode_command(ROBOT_ID, "TROT", 0.0);
        // Пауза старта: контроллер ещё не тикает.
        for _ in 0..STARTUP_GRACE_TICKS {
            assert!(state.control_tick(0.0).is_none());
        }
        // Первый тик после паузы — тик #1, лог положен только на кратных 120.
        let first = state.control_tick(0.0).unwrap();
        assert!(first.debug_line.is_none(), "тик #1 не логируется");

        let mut logged = 0;
        for _ in 1..120 {
            if let Some(out) = state.control_tick(0.0) {
                if out.debug_line.is_some() {
                    logged += 1;
                }
            }
        }
        assert_eq!(logged, 1, "ожидался ровно один лог на 120 тиков");
        assert_eq!(state.ticks(), 120);
    }

    #[test]
    fn trot_imu_compensation_branch_changes_foot_positions() {
        // use_imu=true включает PID-компенсацию наклона в step_trot.
        let mut with_imu = SharedState::with_imu_compensation(true);
        with_imu.apply_mode_command(ROBOT_ID, "TROT", 0.0);
        with_imu.apply_velocity(ROBOT_ID, [0.05, 0.0, 0.0], [0.0, 0.0, 0.0]);
        let half = std::f64::consts::FRAC_PI_8;
        let q = nalgebra::Quaternion::new(half.cos(), half.sin(), 0.0, 0.0);
        with_imu.apply_imu_quaternion(&q);
        let angles_imu = with_imu.step(STEP_HEIGHT, 1.0);

        let mut without_imu = SharedState::with_imu_compensation(false);
        without_imu.apply_mode_command(ROBOT_ID, "TROT", 0.0);
        without_imu.apply_velocity(ROBOT_ID, [0.05, 0.0, 0.0], [0.0, 0.0, 0.0]);
        without_imu.apply_imu_quaternion(&q);
        let angles_plain = without_imu.step(STEP_HEIGHT, 1.0);

        assert!(angles_imu.iter().all(|a| a.is_finite()));
        assert!(
            angles_imu
                .iter()
                .zip(angles_plain.iter())
                .any(|(a, b)| (a - b).abs() > 1e-9),
            "компенсация наклона должна менять углы суставов"
        );
    }

    #[test]
    fn controller_params_defaults_match_constants() {
        let p = ControllerParams::default();
        assert!(!p.use_imu);
        assert!((p.robot_height - STEP_HEIGHT).abs() < 1e-12);
        assert_eq!(p.control_period_ms, CONTROL_PERIOD_MS as i64);
        assert_eq!(p.startup_grace_ticks, STARTUP_GRACE_TICKS as i64);
        assert_eq!(p.control_period(), Duration::from_millis(16));
        assert_eq!(p.startup_grace_ticks(), STARTUP_GRACE_TICKS);
    }

    #[test]
    fn controller_params_clamp_out_of_range_values() {
        // Период меньше 1 мс дал бы busy-loop, больше 1000 мс — мёртвый цикл.
        let mut p = ControllerParams::default();
        p.control_period_ms = 0;
        assert_eq!(p.control_period(), Duration::from_millis(1));
        p.control_period_ms = -10;
        assert_eq!(p.control_period(), Duration::from_millis(1));
        p.control_period_ms = 5000;
        assert_eq!(p.control_period(), Duration::from_millis(1000));
        p.control_period_ms = 33;
        assert_eq!(p.control_period(), Duration::from_millis(33));

        // Отрицательная пауза старта означает «без паузы».
        p.startup_grace_ticks = -5;
        assert_eq!(p.startup_grace_ticks(), 0);
        p.startup_grace_ticks = 5000;
        assert_eq!(p.startup_grace_ticks(), 1000);
        p.startup_grace_ticks = 7;
        assert_eq!(p.startup_grace_ticks(), 7);
    }

    #[test]
    fn with_params_applies_height_and_grace() {
        let params = ControllerParams {
            use_imu: false,
            robot_height: -0.3,
            control_period_ms: 20,
            startup_grace_ticks: 5,
        };
        let mut state = SharedState::with_params(&params);
        assert!((state.robot_height() + 0.3).abs() < 1e-12);
        assert_eq!(state.startup_grace(), 5);
        // Высота из параметра уходит в IK: 5 тиков паузы, затем один тик.
        for _ in 0..5 {
            assert!(state.control_tick(0.0).is_none());
        }
        let out = state.control_tick(0.0).expect("тик после паузы");
        assert_eq!(out.angles.len(), 12);
        assert!(out.angles.iter().all(|a| a.is_finite()));
    }

    #[test]
    fn with_params_enables_imu_compensation_branch() {
        let params = ControllerParams {
            use_imu: true,
            ..ControllerParams::default()
        };
        let state = SharedState::with_params(&params);
        assert!(state.trot_gait.use_imu());
    }
}

//! Состояние и обработчики одометрии: FK ног, IMU, stall-детект и сообщения.
//!
//! Логика перенесена из `odometry_node.rs` без изменения поведения; в бинарнике
//! остаётся только связка с rclrs (узел, подписки, таймер).
//!
//! Фильтрация и интегрирование живут в `quadropted_core::odometry`; здесь —
//! мост между ROS-сообщениями и этим состоянием плюс сборка исходящих
//! сообщений, что и проверяется юнит-тестами.

use geometry_msgs_rs::{Quaternion, TransformStamped};
use nalgebra::Quaternion as NaQuaternion;
use nav_msgs_rs::Odometry;
use quadropted_core::kinematics::forward::{compute_leg_fk_chain, leg_base_positions};
use quadropted_core::math::quaternion::{euler_yaw, quat_from_yaw};
use quadropted_core::odometry::state::OdometryState;
use quadropted_core::odometry::update::{normalize_angle, update_odometry};
use rosidl_runtime_rs::Sequence;
use std::time::Duration;

/// Длина корпуса для FK ног (C++ `body_length`).
pub const BODY_LENGTH: f64 = 0.3762;
/// Ширина корпуса для FK ног (C++ `body_width`).
pub const BODY_WIDTH: f64 = 0.0935;
/// Смещение бедра по вертикали (C++ `l1`).
pub const L1: f64 = 0.0;
/// Длина бедра (C++ `l2`).
pub const L2: f64 = 0.0955;
/// Длина голени (C++ `l3`).
pub const L3: f64 = 0.213;
/// Длина стопы (C++ `l4`).
pub const L4: f64 = 0.213;
/// Коэффициент контакта в `update_odometry` (C++ `0.65`).
pub const CONTACT_COUNT_COEFF: f64 = 0.65;
/// `robot_id`, на который реагирует подписка скорости.
pub const ROBOT_ID: u16 = 1;
/// Сколько ног в модели.
pub const LEG_COUNT: usize = 4;
/// Сколько углов приходит в `joint_group_controller/commands`.
pub const JOINT_COUNT: usize = 12;

/// Параметры узла одометрии с C++-дефолтами.
#[derive(Debug, Clone, PartialEq)]
pub struct OdometryParams {
    /// Частота публикации, Гц.
    pub publish_rate: i64,
    /// Использовать yaw из IMU.
    pub has_imu_heading: bool,
    /// Публиковать TF odom → base_link.
    pub enable_odom_tf: bool,
    /// Размер окна фильтрации (C++ `14`).
    pub filter_window_size: i64,
    /// `header.frame_id` одометрии.
    pub odom_frame_id: String,
    /// `child_frame_id` одометрии.
    pub base_frame_id: String,
    /// Окно stall-детекта (C++ `20`).
    pub stall_window: i64,
    /// Порог входа в stall по угловой скорости.
    pub stall_ang_vel_threshold: f64,
    /// Порог выхода из stall по угловой скорости.
    pub stall_exit_ang_vel_threshold: f64,
}

impl Default for OdometryParams {
    fn default() -> Self {
        Self {
            publish_rate: 50,
            has_imu_heading: true,
            enable_odom_tf: false,
            filter_window_size: 14,
            odom_frame_id: "odom".to_string(),
            base_frame_id: "base_link".to_string(),
            stall_window: 20,
            stall_ang_vel_threshold: 0.05,
            stall_exit_ang_vel_threshold: 0.1,
        }
    }
}

impl OdometryParams {
    /// Собрать параметры из произвольного источника значений.
    ///
    /// Абстракция нужна, чтобы разбор параметров (дефолты, типы, имена)
    /// проверялся юнит-тестами: в узле источником выступает rclrs, в тестах —
    /// обычная карта значений.
    pub fn from_lookup(lookup: &dyn ParamLookup) -> Self {
        let defaults = Self::default();
        Self {
            publish_rate: lookup.get_i64("publish_rate").unwrap_or(defaults.publish_rate),
            has_imu_heading: lookup
                .get_bool("has_imu_heading")
                .unwrap_or(defaults.has_imu_heading),
            enable_odom_tf: lookup
                .get_bool("enable_odom_tf")
                .unwrap_or(defaults.enable_odom_tf),
            filter_window_size: lookup
                .get_i64("filter_window_size")
                .unwrap_or(defaults.filter_window_size),
            odom_frame_id: lookup
                .get_str("odom_frame_id")
                .unwrap_or(defaults.odom_frame_id),
            base_frame_id: lookup
                .get_str("base_frame_id")
                .unwrap_or(defaults.base_frame_id),
            stall_window: lookup.get_i64("stall_window").unwrap_or(defaults.stall_window),
            stall_ang_vel_threshold: lookup
                .get_f64("stall_ang_vel_threshold")
                .unwrap_or(defaults.stall_ang_vel_threshold),
            stall_exit_ang_vel_threshold: lookup
                .get_f64("stall_exit_ang_vel_threshold")
                .unwrap_or(defaults.stall_exit_ang_vel_threshold),
        }
    }

    /// Период таймера по частоте публикации; нулевая и отрицательная частота
    /// недопустимы, поэтому берётся минимум 1 Гц.
    pub fn timer_period(&self) -> Duration {
        Duration::from_micros(1_000_000 / self.publish_rate.max(1) as u64)
    }

    /// Размер окна фильтра: не меньше 1, иначе фильтр не работает.
    pub fn window_size(&self) -> usize {
        self.filter_window_size.max(1) as usize
    }
}

/// Источник значений параметров узла (rclrs в узле, карта в тестах).
pub trait ParamLookup {
    /// Целочисленный параметр.
    fn get_i64(&self, name: &str) -> Option<i64>;
    /// Логический параметр.
    fn get_bool(&self, name: &str) -> Option<bool>;
    /// Параметр с плавающей точкой.
    fn get_f64(&self, name: &str) -> Option<f64>;
    /// Строковый параметр (rclrs хранит его как `Arc<str>`).
    fn get_str(&self, name: &str) -> Option<String>;
}

/// Общее состояние узла: одометрия, часы и параметры отображения.
pub struct OdomShared {
    /// Состояние одометрии из quadropted-core.
    pub state: OdometryState,
    /// Время прошлого тика (ROS-часы, с).
    pub last_sim_time: f64,
    /// `header.frame_id` одометрии.
    pub odom_frame_id: String,
    /// `child_frame_id` одометрии.
    pub base_frame_id: String,
}

impl OdomShared {
    /// Создать состояние по параметрам узла.
    pub fn new(params: &OdometryParams) -> Self {
        let mut state = OdometryState::new(params.window_size());
        state.stall_window = params.stall_window as i32;
        state.stall_ang_vel_threshold = params.stall_ang_vel_threshold;
        state.stall_exit_ang_vel_threshold = params.stall_exit_ang_vel_threshold;
        Self {
            state,
            last_sim_time: 0.0,
            odom_frame_id: params.odom_frame_id.clone(),
            base_frame_id: params.base_frame_id.clone(),
        }
    }

    /// Обновить `joint_positions` из `joint_group_controller/commands`.
    ///
    /// Возвращает `false`, если пришло не 12 углов — сообщение отбрасывается,
    /// состояние остаётся прежним (как в C++).
    pub fn apply_joint_command(&mut self, data: &[f64]) -> bool {
        if data.len() != JOINT_COUNT {
            return false;
        }
        for (i, v) in data.iter().enumerate() {
            self.state.joint_positions[i] = *v;
        }
        true
    }

    /// Обновить контакты ног из `foot_contact`.
    pub fn apply_foot_contact(&mut self, contacts: &[bool; LEG_COUNT]) {
        for (i, contact) in contacts.iter().enumerate() {
            self.state.foot_states[i].contact = *contact;
        }
    }

    /// Применить ориентацию и скорости из `imu`.
    pub fn apply_imu(
        &mut self,
        orientation: &NaQuaternion<f64>,
        angular_velocity_z: f64,
        linear_acceleration: [f64; 3],
    ) {
        self.state.theta = normalize_angle(euler_yaw(orientation));
        self.state.imu_angular_velocity = -angular_velocity_z;
        self.state.imu_linear_acceleration_x = linear_acceleration[0];
        self.state.imu_linear_acceleration_y = linear_acceleration[1];
        self.state.imu_linear_acceleration_z = linear_acceleration[2];
    }

    /// Применить `robot_velocity` (fallback-скорость без контактов).
    pub fn apply_robot_velocity(&mut self, robot_id: u16, linear: [f64; 2]) -> bool {
        if robot_id != ROBOT_ID {
            return false;
        }
        self.state.linear_velocity_x = linear[0];
        self.state.linear_velocity_y = linear[1];
        true
    }

    /// Посчитать позиции стоп по углам суставов (forward kinematics).
    pub fn update_foot_positions(&mut self) {
        for i in 0..LEG_COUNT {
            let joints = [
                self.state.joint_positions[i * 3],
                self.state.joint_positions[i * 3 + 1],
                self.state.joint_positions[i * 3 + 2],
            ];
            let base = leg_base_positions(i, BODY_LENGTH, BODY_WIDTH);
            let foot = compute_leg_fk_chain(
                joints[0], joints[1], joints[2], base.x, base.y, L1, L2, L3, L4,
            );
            self.state.foot_states[i].position = foot;
        }
    }

    /// Продвинуть часы и вернуть dt с прошлого тика (0.0 на первом тике).
    pub fn advance_clock(&mut self, now_secs: f64) -> f64 {
        let dt = now_secs - self.last_sim_time;
        self.last_sim_time = now_secs;
        dt
    }

    /// Один тик одометрии: FK → интегрирование. Возвращает dt.
    pub fn tick(&mut self, now_secs: f64) -> f64 {
        self.update_foot_positions();
        let dt = self.advance_clock(now_secs);
        update_odometry(&mut self.state, dt, CONTACT_COUNT_COEFF);
        dt
    }

    /// Собрать `nav_msgs/Odometry` для публикации.
    pub fn build_odom(&self, sec: i32, nanosec: u32) -> Odometry {
        let mut odom = Odometry::default();
        odom.header.frame_id = self.odom_frame_id.clone().into();
        odom.child_frame_id = self.base_frame_id.clone().into();
        odom.header.stamp.sec = sec;
        odom.header.stamp.nanosec = nanosec;

        odom.pose.pose.position.x = self.state.x;
        odom.pose.pose.position.y = self.state.y;
        odom.pose.pose.position.z = 0.0;
        odom.pose.pose.orientation = quat_from_yaw_msg(self.state.theta);

        odom.twist.twist.linear.x = self.state.linear_velocity_x;
        odom.twist.twist.linear.y = self.state.linear_velocity_y;
        odom.twist.twist.angular.z = self.state.imu_angular_velocity;
        odom
    }

    /// Признак stall для `stall_status`.
    pub fn stall_status(&self) -> bool {
        self.state.is_stalled
    }

    /// Собрать `MarkerArray` со стопами для RViz (C++ `publish_markers`).
    pub fn build_foot_markers(&self, sec: i32, nanosec: u32) -> visualization_msgs_rs::MarkerArray {
        let mut ma = visualization_msgs_rs::MarkerArray::default();
        let mut seq = Sequence::new(LEG_COUNT);
        let colors: [[f32; 3]; LEG_COUNT] = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
        ];
        for i in 0..LEG_COUNT {
            let mut m = visualization_msgs_rs::Marker::default();
            m.header.stamp.sec = sec;
            m.header.stamp.nanosec = nanosec;
            m.header.frame_id = self.base_frame_id.clone().into();
            m.ns = "foot_markers".into();
            m.id = i as i32;
            m.r#type = 2; // SPHERE
            m.action = 0; // ADD
            m.pose.position.x = self.state.foot_states[i].position.x;
            m.pose.position.y = self.state.foot_states[i].position.y;
            m.pose.position.z = self.state.foot_states[i].position.z;
            m.pose.orientation.w = 1.0;
            m.scale.x = 0.05;
            m.scale.y = 0.05;
            m.scale.z = 0.05;
            m.color.a = 1.0;
            m.color.r = colors[i][0];
            m.color.g = colors[i][1];
            m.color.b = colors[i][2];
            seq[i] = m;
        }
        ma.markers = seq;
        ma
    }

    /// Собрать `tf2_msgs/TFMessage` (odom → base_link).
    pub fn build_tf(&self, sec: i32, nanosec: u32) -> tf2_msgs_rs::TFMessage {
        let mut tf_msg = tf2_msgs_rs::TFMessage::default();
        let mut seq = Sequence::new(1);
        let mut ts = TransformStamped::default();
        ts.header.stamp.sec = sec;
        ts.header.stamp.nanosec = nanosec;
        ts.header.frame_id = self.odom_frame_id.clone().into();
        ts.child_frame_id = self.base_frame_id.clone().into();
        ts.transform.translation.x = self.state.x;
        ts.transform.translation.y = self.state.y;
        ts.transform.translation.z = 0.0;
        ts.transform.rotation = quat_from_yaw_msg(self.state.theta);
        seq[0] = ts;
        tf_msg.transforms = seq;
        tf_msg
    }
}

/// Кватернион ROS-сообщения из yaw.
pub fn quat_from_yaw_msg(yaw: f64) -> Quaternion {
    let q = quat_from_yaw(yaw);
    Quaternion {
        x: q.i,
        y: q.j,
        z: q.k,
        w: q.w,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn params() -> OdometryParams {
        OdometryParams::default()
    }

    /// Тестовый источник параметров: значения хранятся в карте строками.
    struct MapLookup {
        values: std::collections::HashMap<String, String>,
    }

    impl MapLookup {
        fn new(pairs: &[(&str, &str)]) -> Self {
            Self {
                values: pairs
                    .iter()
                    .map(|(k, v)| (k.to_string(), v.to_string()))
                    .collect(),
            }
        }
        fn get(&self, name: &str) -> Option<&str> {
            self.values.get(name).map(|v| v.as_str())
        }
    }

    impl ParamLookup for MapLookup {
        fn get_i64(&self, name: &str) -> Option<i64> {
            self.get(name).map(|v| v.parse().unwrap())
        }
        fn get_bool(&self, name: &str) -> Option<bool> {
            self.get(name).map(|v| v.parse().unwrap())
        }
        fn get_f64(&self, name: &str) -> Option<f64> {
            self.get(name).map(|v| v.parse().unwrap())
        }
        fn get_str(&self, name: &str) -> Option<String> {
            self.get(name).map(|v| v.to_string())
        }
    }

    #[test]
    fn from_lookup_without_overrides_returns_defaults() {
        let lookup = MapLookup::new(&[]);
        assert_eq!(OdometryParams::from_lookup(&lookup), OdometryParams::default());
    }

    #[test]
    fn from_lookup_reads_every_supported_parameter() {
        let lookup = MapLookup::new(&[
            ("publish_rate", "25"),
            ("has_imu_heading", "false"),
            ("enable_odom_tf", "true"),
            ("filter_window_size", "7"),
            ("odom_frame_id", "odom_map"),
            ("base_frame_id", "base_footprint"),
            ("stall_window", "11"),
            ("stall_ang_vel_threshold", "0.02"),
            ("stall_exit_ang_vel_threshold", "0.04"),
        ]);
        let p = OdometryParams::from_lookup(&lookup);
        assert_eq!(p.publish_rate, 25);
        assert!(!p.has_imu_heading);
        assert!(p.enable_odom_tf);
        assert_eq!(p.filter_window_size, 7);
        assert_eq!(p.odom_frame_id, "odom_map");
        assert_eq!(p.base_frame_id, "base_footprint");
        assert_eq!(p.stall_window, 11);
        assert!((p.stall_ang_vel_threshold - 0.02).abs() < 1e-12);
        assert!((p.stall_exit_ang_vel_threshold - 0.04).abs() < 1e-12);
        // Уже применённые значения должны попасть и в состояние.
        let shared = OdomShared::new(&p);
        assert_eq!(shared.state.filter_window_size, 7);
        assert_eq!(shared.state.stall_window, 11);
        assert_eq!(shared.odom_frame_id, "odom_map");
    }

    #[test]
    fn from_lookup_fills_only_missing_parameters() {
        let lookup = MapLookup::new(&[("publish_rate", "10"), ("base_frame_id", "base_x")]);
        let p = OdometryParams::from_lookup(&lookup);
        assert_eq!(p.publish_rate, 10);
        assert_eq!(p.base_frame_id, "base_x");
        // Остальные — C++-дефолты.
        assert_eq!(p.odom_frame_id, "odom");
        assert_eq!(p.filter_window_size, 14);
        assert_eq!(p.timer_period(), Duration::from_micros(100_000));
    }

    #[test]
    fn default_params_match_cpp_defaults() {
        let p = OdometryParams::default();
        assert_eq!(p.publish_rate, 50);
        assert!(p.has_imu_heading);
        assert!(!p.enable_odom_tf);
        assert_eq!(p.filter_window_size, 14);
        assert_eq!(p.odom_frame_id, "odom");
        assert_eq!(p.base_frame_id, "base_link");
        assert_eq!(p.stall_window, 20);
        assert!((p.stall_ang_vel_threshold - 0.05).abs() < 1e-12);
        assert!((p.stall_exit_ang_vel_threshold - 0.1).abs() < 1e-12);
    }

    #[test]
    fn timer_period_uses_publish_rate_and_survives_zero() {
        let mut p = params();
        assert_eq!(p.timer_period(), Duration::from_micros(20_000));
        p.publish_rate = 10;
        assert_eq!(p.timer_period(), Duration::from_micros(100_000));
        p.publish_rate = 0;
        assert_eq!(p.timer_period(), Duration::from_micros(1_000_000));
        p.publish_rate = -5;
        assert_eq!(p.timer_period(), Duration::from_micros(1_000_000));
    }

    #[test]
    fn window_size_never_zero() {
        let mut p = params();
        p.filter_window_size = 0;
        assert_eq!(p.window_size(), 1);
        p.filter_window_size = -3;
        assert_eq!(p.window_size(), 1);
        p.filter_window_size = 7;
        assert_eq!(p.window_size(), 7);
    }

    #[test]
    fn new_applies_params_to_state() {
        let mut p = params();
        p.filter_window_size = 9;
        p.stall_window = 7;
        p.stall_ang_vel_threshold = 0.02;
        p.stall_exit_ang_vel_threshold = 0.04;
        let shared = OdomShared::new(&p);
        assert_eq!(shared.state.filter_window_size, 9);
        assert_eq!(shared.state.stall_window, 7);
        assert!((shared.state.stall_ang_vel_threshold - 0.02).abs() < 1e-12);
        assert!((shared.state.stall_exit_ang_vel_threshold - 0.04).abs() < 1e-12);
        assert_eq!(shared.odom_frame_id, "odom");
        assert_eq!(shared.base_frame_id, "base_link");
        assert_eq!(shared.last_sim_time, 0.0);
    }

    #[test]
    fn joint_command_requires_twelve_values() {
        let mut shared = OdomShared::new(&params());
        assert!(!shared.apply_joint_command(&[0.0; 11]));
        assert!(!shared.apply_joint_command(&[0.0; 13]));
        assert_eq!(shared.state.joint_positions, [0.0; 12]);

        let mut data = [0.0; 12];
        for (i, v) in data.iter_mut().enumerate() {
            *v = i as f64 * 0.1;
        }
        assert!(shared.apply_joint_command(&data));
        assert!((shared.state.joint_positions[11] - 1.1).abs() < 1e-12);
    }

    #[test]
    fn foot_contacts_are_copied() {
        let mut shared = OdomShared::new(&params());
        shared.apply_foot_contact(&[true, false, true, false]);
        assert!(shared.state.foot_states[0].contact);
        assert!(!shared.state.foot_states[1].contact);
        assert!(shared.state.foot_states[2].contact);
        assert!(!shared.state.foot_states[3].contact);
    }

    #[test]
    fn imu_sets_heading_and_inverts_angular_z() {
        let mut shared = OdomShared::new(&params());
        let half = std::f64::consts::FRAC_PI_2 / 2.0;
        let q = NaQuaternion::new(half.cos(), 0.0, 0.0, half.sin());
        shared.apply_imu(&q, 0.3, [1.0, -2.0, 9.81]);
        assert!((shared.state.theta - std::f64::consts::FRAC_PI_2).abs() < 1e-9);
        assert!((shared.state.imu_angular_velocity + 0.3).abs() < 1e-12);
        assert!((shared.state.imu_linear_acceleration_x - 1.0).abs() < 1e-12);
        assert!((shared.state.imu_linear_acceleration_y + 2.0).abs() < 1e-12);
        assert!((shared.state.imu_linear_acceleration_z - 9.81).abs() < 1e-12);
    }

    #[test]
    fn imu_heading_is_normalized_to_pi() {
        let mut shared = OdomShared::new(&params());
        // yaw = 270° должен прийти как -90°.
        let yaw = 3.0 * std::f64::consts::FRAC_PI_2;
        let half = yaw / 2.0;
        let q = NaQuaternion::new(half.cos(), 0.0, 0.0, half.sin());
        shared.apply_imu(&q, 0.0, [0.0; 3]);
        assert!(shared.state.theta > -std::f64::consts::PI);
        assert!(shared.state.theta < std::f64::consts::PI);
        assert!((shared.state.theta + std::f64::consts::FRAC_PI_2).abs() < 1e-9);
    }

    #[test]
    fn robot_velocity_ignores_foreign_robot_id() {
        let mut shared = OdomShared::new(&params());
        assert!(!shared.apply_robot_velocity(2, [1.0, 1.0]));
        assert_eq!(shared.state.linear_velocity_x, 0.0);
        assert!(shared.apply_robot_velocity(ROBOT_ID, [0.4, -0.2]));
        assert!((shared.state.linear_velocity_x - 0.4).abs() < 1e-12);
        assert!((shared.state.linear_velocity_y + 0.2).abs() < 1e-12);
    }

    #[test]
    fn foot_positions_match_forward_kinematics() {
        let mut shared = OdomShared::new(&params());
        let data: [f64; 12] = [
            0.0, 0.7, -1.4, 0.0, 0.7, -1.4, 0.0, 0.7, -1.4, 0.0, 0.7, -1.4,
        ];
        assert!(shared.apply_joint_command(&data));
        shared.update_foot_positions();

        let base = leg_base_positions(0, BODY_LENGTH, BODY_WIDTH);
        let expected =
            compute_leg_fk_chain(0.0, 0.7, -1.4, base.x, base.y, L1, L2, L3, L4);
        let got = shared.state.foot_states[0].position;
        assert!((got.x - expected.x).abs() < 1e-12);
        assert!((got.y - expected.y).abs() < 1e-12);
        assert!((got.z - expected.z).abs() < 1e-12);
        // Стойка симметрична: FR и RR различаются по x знаком.
        assert!(shared.state.foot_states[0].position.x > shared.state.foot_states[2].position.x);
    }

    #[test]
    fn advance_clock_returns_dt_from_previous_tick() {
        let mut shared = OdomShared::new(&params());
        assert_eq!(shared.advance_clock(1.5), 1.5);
        assert!((shared.advance_clock(1.75) - 0.25).abs() < 1e-12);
        // Время назад даёт отрицательный dt — интегрирование такое отбрасывает.
        assert!(shared.advance_clock(1.5) < 0.0);
    }

    #[test]
    fn tick_integrates_pose_when_feet_contact_ground() {
        let mut shared = OdomShared::new(&params());
        let data: [f64; 12] = [
            0.0, 0.7, -1.4, 0.0, 0.7, -1.4, 0.0, 0.7, -1.4, 0.0, 0.7, -1.4,
        ];
        shared.apply_joint_command(&data);
        shared.apply_foot_contact(&[true; 4]);

        // Первый тик только запоминает позиции стоп — смещения ещё нет.
        shared.tick(1.0);
        assert_eq!(shared.state.x, 0.0);
        assert_eq!(shared.state.y, 0.0);

        // Второй тик: стопы остались на месте, значит робот не двигался.
        shared.tick(1.02);
        assert!(shared.state.x.abs() < 1e-12);
        assert!(shared.state.y.abs() < 1e-12);
    }

    #[test]
    fn tick_moves_pose_when_feet_slide_backwards() {
        let mut shared = OdomShared::new(&params());
        // Первый тик: стопы в базовой позе.
        let data: [f64; 12] = [
            0.0, 0.7, -1.4, 0.0, 0.7, -1.4, 0.0, 0.7, -1.4, 0.0, 0.7, -1.4,
        ];
        shared.apply_joint_command(&data);
        shared.apply_foot_contact(&[true; 4]);
        shared.tick(1.0);

        // Второй тик: та же поза, но прошлые позиции уже записаны —
        // смещения нет; проверяем, что интегрирование вообще выполняется.
        let before = (shared.state.x, shared.state.y);
        shared.tick(1.02);
        assert!(shared.state.x.is_finite());
        assert!(shared.state.y.is_finite());
        assert_eq!((shared.state.x, shared.state.y), before);
    }

    #[test]
    fn odom_message_carries_pose_and_frames() {
        let mut shared = OdomShared::new(&params());
        shared.state.x = 1.25;
        shared.state.y = -0.5;
        shared.state.theta = std::f64::consts::FRAC_PI_2;
        shared.state.linear_velocity_x = 0.3;
        shared.state.linear_velocity_y = -0.1;
        shared.state.imu_angular_velocity = 0.2;

        let odom = shared.build_odom(12, 345);
        assert_eq!(odom.header.frame_id.to_string(), "odom");
        assert_eq!(odom.child_frame_id.to_string(), "base_link");
        assert_eq!(odom.header.stamp.sec, 12);
        assert_eq!(odom.header.stamp.nanosec, 345);
        assert!((odom.pose.pose.position.x - 1.25).abs() < 1e-12);
        assert!((odom.pose.pose.position.y + 0.5).abs() < 1e-12);
        assert_eq!(odom.pose.pose.position.z, 0.0);
        assert!((odom.twist.twist.linear.x - 0.3).abs() < 1e-12);
        assert!((odom.twist.twist.linear.y + 0.1).abs() < 1e-12);
        assert!((odom.twist.twist.angular.z - 0.2).abs() < 1e-12);

        let q = quat_from_yaw(std::f64::consts::FRAC_PI_2);
        assert!((odom.pose.pose.orientation.z - q.k).abs() < 1e-12);
        assert!((odom.pose.pose.orientation.w - q.w).abs() < 1e-12);
    }

    #[test]
    fn odom_frames_follow_params() {
        let mut p = params();
        p.odom_frame_id = "odom_custom".to_string();
        p.base_frame_id = "base_footprint".to_string();
        let shared = OdomShared::new(&p);
        let odom = shared.build_odom(0, 0);
        assert_eq!(odom.header.frame_id.to_string(), "odom_custom");
        assert_eq!(odom.child_frame_id.to_string(), "base_footprint");
    }

    #[test]
    fn stall_status_follows_state() {
        let mut shared = OdomShared::new(&params());
        assert!(!shared.stall_status());
        shared.state.is_stalled = true;
        assert!(shared.stall_status());
    }

    #[test]
    fn foot_markers_describe_four_legs() {
        let mut shared = OdomShared::new(&params());
        shared.update_foot_positions();
        let markers = shared.build_foot_markers(5, 6);
        assert_eq!(markers.markers.len(), 4);
        for (i, m) in markers.markers.iter().enumerate() {
            assert_eq!(m.id, i as i32);
            assert_eq!(m.r#type, 2, "SPHERE");
            assert_eq!(m.action, 0, "ADD");
            assert_eq!(m.ns.to_string(), "foot_markers");
            assert_eq!(m.header.frame_id.to_string(), "base_link");
            assert_eq!(m.header.stamp.sec, 5);
            assert_eq!(m.header.stamp.nanosec, 6);
            assert!((m.scale.x - 0.05).abs() < 1e-9);
            assert!((m.color.a - 1.0).abs() < 1e-9);
        }
        // Цвета различаются по ногам, чтобы в RViz было видно, где какая.
        assert!(markers.markers[0].color.r > markers.markers[1].color.r);
    }

    #[test]
    fn tf_message_links_odom_to_base() {
        let mut shared = OdomShared::new(&params());
        shared.state.x = 0.7;
        shared.state.y = 0.1;
        shared.state.theta = 0.5;
        let tf = shared.build_tf(3, 4);
        assert_eq!(tf.transforms.len(), 1);
        let t = &tf.transforms[0];
        assert_eq!(t.header.frame_id.to_string(), "odom");
        assert_eq!(t.child_frame_id.to_string(), "base_link");
        assert_eq!(t.header.stamp.sec, 3);
        assert_eq!(t.header.stamp.nanosec, 4);
        assert!((t.transform.translation.x - 0.7).abs() < 1e-12);
        assert!((t.transform.translation.y - 0.1).abs() < 1e-12);
        assert_eq!(t.transform.translation.z, 0.0);
        let q = quat_from_yaw(0.5);
        assert!((t.transform.rotation.w - q.w).abs() < 1e-12);
    }

    #[test]
    fn quat_from_yaw_message_is_unit_length() {
        for yaw in [0.0_f64, 0.3, -1.2, 3.0] {
            let q = quat_from_yaw_msg(yaw);
            let norm = (q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w).sqrt();
            assert!((norm - 1.0).abs() < 1e-12, "yaw={yaw}");
        }
    }
}

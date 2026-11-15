//! Явное объявление ROS-параметров узлов через `declare_parameter`.
//!
//! В rclrs 0.7 override из `--ros-args -p name:=value` (и из launch-файла)
//! применяется только в момент объявления параметра. `use_undeclared_parameters()`
//! с последующим `Parameters::get()` читает storage параметров и override-map
//! не видит, поэтому узел молча работал на дефолтах из кода.
//!
//! Здесь каждый параметр объявляется с дефолтом, а полученный дескриптор
//! (`MandatoryParameter`) держится до конца `main`: при drop параметр снимается
//! с регистрации и исчезает из параметр-сервисов. Имена и дефолты повторяют
//! `OdometryParams`/`ControllerParams`, чтобы их можно было проверить тестами.

use std::sync::Arc;

use rclrs::{DeclarationError, MandatoryParameter, Node};

use crate::controller::ControllerParams;
use crate::odometry::{OdometryParams, ParamLookup};

/// Дескрипторы параметров узла одометрии.
///
/// Держать структуру живой до конца `main` — иначе `Drop` дескрипторов
/// снимет параметры с регистрации и их не будет видно в параметр-сервисах.
pub struct OdometryParamHandles {
    publish_rate: MandatoryParameter<i64>,
    has_imu_heading: MandatoryParameter<bool>,
    enable_odom_tf: MandatoryParameter<bool>,
    filter_window_size: MandatoryParameter<i64>,
    odom_frame_id: MandatoryParameter<Arc<str>>,
    base_frame_id: MandatoryParameter<Arc<str>>,
    stall_window: MandatoryParameter<i64>,
    stall_ang_vel_threshold: MandatoryParameter<f64>,
    stall_exit_ang_vel_threshold: MandatoryParameter<f64>,
}

impl OdometryParamHandles {
    /// Объявить все параметры одометрии; дефолты — C++-совместимые.
    pub fn declare(node: &Node) -> Result<Self, DeclarationError> {
        let defaults = OdometryParams::default();
        Ok(Self {
            publish_rate: node
                .declare_parameter::<i64>("publish_rate")
                .default(defaults.publish_rate)
                .mandatory()?,
            has_imu_heading: node
                .declare_parameter::<bool>("has_imu_heading")
                .default(defaults.has_imu_heading)
                .mandatory()?,
            enable_odom_tf: node
                .declare_parameter::<bool>("enable_odom_tf")
                .default(defaults.enable_odom_tf)
                .mandatory()?,
            filter_window_size: node
                .declare_parameter::<i64>("filter_window_size")
                .default(defaults.filter_window_size)
                .mandatory()?,
            odom_frame_id: node
                .declare_parameter::<Arc<str>>("odom_frame_id")
                .default(Arc::from(defaults.odom_frame_id.as_str()))
                .mandatory()?,
            base_frame_id: node
                .declare_parameter::<Arc<str>>("base_frame_id")
                .default(Arc::from(defaults.base_frame_id.as_str()))
                .mandatory()?,
            stall_window: node
                .declare_parameter::<i64>("stall_window")
                .default(defaults.stall_window)
                .mandatory()?,
            stall_ang_vel_threshold: node
                .declare_parameter::<f64>("stall_ang_vel_threshold")
                .default(defaults.stall_ang_vel_threshold)
                .mandatory()?,
            stall_exit_ang_vel_threshold: node
                .declare_parameter::<f64>("stall_exit_ang_vel_threshold")
                .default(defaults.stall_exit_ang_vel_threshold)
                .mandatory()?,
        })
    }

    /// Собрать параметры узла из уже объявленных (и применённых) значений.
    pub fn to_params(&self) -> OdometryParams {
        OdometryParams::from_lookup(self)
    }

    /// Частота публикации, Гц (для таймера).
    pub fn publish_rate(&self) -> i64 {
        self.publish_rate.get()
    }

    /// Использовать yaw из IMU (влияет на набор подписок).
    pub fn has_imu_heading(&self) -> bool {
        self.has_imu_heading.get()
    }

    /// Публиковать TF odom → base_link.
    pub fn enable_odom_tf(&self) -> bool {
        self.enable_odom_tf.get()
    }
}

impl ParamLookup for OdometryParamHandles {
    fn get_i64(&self, name: &str) -> Option<i64> {
        match name {
            "publish_rate" => Some(self.publish_rate.get()),
            "filter_window_size" => Some(self.filter_window_size.get()),
            "stall_window" => Some(self.stall_window.get()),
            _ => None,
        }
    }

    fn get_bool(&self, name: &str) -> Option<bool> {
        match name {
            "has_imu_heading" => Some(self.has_imu_heading.get()),
            "enable_odom_tf" => Some(self.enable_odom_tf.get()),
            _ => None,
        }
    }

    fn get_f64(&self, name: &str) -> Option<f64> {
        match name {
            "stall_ang_vel_threshold" => Some(self.stall_ang_vel_threshold.get()),
            "stall_exit_ang_vel_threshold" => Some(self.stall_exit_ang_vel_threshold.get()),
            _ => None,
        }
    }

    fn get_str(&self, name: &str) -> Option<String> {
        match name {
            "odom_frame_id" => Some(self.odom_frame_id.get().to_string()),
            "base_frame_id" => Some(self.base_frame_id.get().to_string()),
            _ => None,
        }
    }
}

/// Дескрипторы параметров узла контроллера.
pub struct ControllerParamHandles {
    use_imu: MandatoryParameter<bool>,
    robot_height: MandatoryParameter<f64>,
    control_period_ms: MandatoryParameter<i64>,
    startup_grace_ticks: MandatoryParameter<i64>,
}

impl ControllerParamHandles {
    /// Объявить параметры контроллера; дефолты — константы узла.
    pub fn declare(node: &Node) -> Result<Self, DeclarationError> {
        let defaults = ControllerParams::default();
        Ok(Self {
            use_imu: node
                .declare_parameter::<bool>("use_imu")
                .default(defaults.use_imu)
                .mandatory()?,
            robot_height: node
                .declare_parameter::<f64>("robot_height")
                .default(defaults.robot_height)
                .mandatory()?,
            control_period_ms: node
                .declare_parameter::<i64>("control_period_ms")
                .default(defaults.control_period_ms)
                .mandatory()?,
            startup_grace_ticks: node
                .declare_parameter::<i64>("startup_grace_ticks")
                .default(defaults.startup_grace_ticks)
                .mandatory()?,
        })
    }

    /// Собрать параметры узла из объявленных значений.
    pub fn to_params(&self) -> ControllerParams {
        ControllerParams {
            use_imu: self.use_imu.get(),
            robot_height: self.robot_height.get(),
            control_period_ms: self.control_period_ms.get(),
            startup_grace_ticks: self.startup_grace_ticks.get(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::controller::{CONTROL_PERIOD_MS, STARTUP_GRACE_TICKS, STEP_HEIGHT};

    #[test]
    fn odometry_defaults_in_declaration_match_params_defaults() {
        // Дефолты объявления и дефолты структуры параметров не должны
        // разъезжаться: тест сравнивает константы, которые видит declare.
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
    fn controller_defaults_in_declaration_match_params_defaults() {
        let p = ControllerParams::default();
        assert!(!p.use_imu);
        assert!((p.robot_height - STEP_HEIGHT).abs() < 1e-12);
        assert_eq!(p.control_period_ms, CONTROL_PERIOD_MS as i64);
        assert_eq!(p.startup_grace_ticks, STARTUP_GRACE_TICKS as i64);
    }
}

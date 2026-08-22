//! Rust bindings for sensor_msgs
//!
//! Provides Imu message type.

use rosidl_runtime_rs::{Message, RmwMessage, Sequence, SequenceAlloc};
use geometry_msgs_rs::{Vector3, Quaternion};

// ========================= std_msgs/msg/Header =========================

#[repr(C)]
pub struct Header {
    pub stamp: builtin_interfaces::Time,
    pub frame_id: rosidl_runtime_rs::String,
}

impl Default for Header {
    fn default() -> Self {
        unsafe { std::mem::zeroed() }
    }
}

impl Clone for Header {
    fn clone(&self) -> Self {
        Self {
            stamp: self.stamp,
            frame_id: self.frame_id.clone(),
        }
    }
}

impl std::fmt::Debug for Header {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Header")
            .field("stamp", &self.stamp)
            .field("frame_id", &self.frame_id.to_cstr())
            .finish()
    }
}

pub mod builtin_interfaces {
    #[repr(C)]
    #[derive(Debug, Clone, Copy)]
    pub struct Time {
        pub sec: i32,
        pub nanosec: u32,
    }
}

// ========================= sensor_msgs/msg/Imu =========================

#[link(name = "sensor_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn sensor_msgs__msg__Imu__init(msg: *mut Imu) -> bool;
    fn sensor_msgs__msg__Imu__fini(msg: *mut Imu);
    fn sensor_msgs__msg__Imu__Sequence__init(seq: *mut Sequence<Imu>, size: usize) -> bool;
    fn sensor_msgs__msg__Imu__Sequence__fini(seq: *mut Sequence<Imu>);
}

#[repr(C)]
pub struct Imu {
    pub header: Header,
    pub orientation: Quaternion,
    pub orientation_covariance: [f64; 9],
    pub angular_velocity: Vector3,
    pub angular_velocity_covariance: [f64; 9],
    pub linear_acceleration: Vector3,
    pub linear_acceleration_covariance: [f64; 9],
}

impl Default for Imu {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !sensor_msgs__msg__Imu__init(&mut msg as *mut _) {
                panic!("Imu__init failed");
            }
            msg
        }
    }
}

impl Clone for Imu {
    fn clone(&self) -> Self {
        Self {
            header: self.header.clone(),
            orientation: self.orientation.clone(),
            orientation_covariance: self.orientation_covariance,
            angular_velocity: self.angular_velocity.clone(),
            angular_velocity_covariance: self.angular_velocity_covariance,
            linear_acceleration: self.linear_acceleration.clone(),
            linear_acceleration_covariance: self.linear_acceleration_covariance,
        }
    }
}

impl std::fmt::Debug for Imu {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Imu")
            .field("header", &self.header)
            .field("orientation", &self.orientation)
            .finish()
    }
}

impl Drop for Imu {
    fn drop(&mut self) {
        unsafe {
            sensor_msgs__msg__Imu__fini(self as *mut _);
        }
    }
}

impl SequenceAlloc for Imu {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { sensor_msgs__msg__Imu__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { sensor_msgs__msg__Imu__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for Imu {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for Imu
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "sensor_msgs/msg/Imu";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__sensor_msgs__msg__Imu()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__sensor_msgs__msg__Imu()
        }
    }
}

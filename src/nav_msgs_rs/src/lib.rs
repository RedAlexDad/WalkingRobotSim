//! Rust bindings for nav_msgs
//!
//! Provides nav_msgs/msg/Odometry message type.

use geometry_msgs_rs::{Point, Pose, PoseWithCovariance, Twist, TwistWithCovariance};
use rosidl_runtime_rs::{Message, RmwMessage, Sequence, SequenceAlloc};
use sensor_msgs_rs::Header;

// ========================= nav_msgs/msg/Odometry =========================

#[link(name = "nav_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn nav_msgs__msg__Odometry__init(msg: *mut Odometry) -> bool;
    fn nav_msgs__msg__Odometry__fini(msg: *mut Odometry);
    fn nav_msgs__msg__Odometry__Sequence__init(seq: *mut Sequence<Odometry>, size: usize) -> bool;
    fn nav_msgs__msg__Odometry__Sequence__fini(seq: *mut Sequence<Odometry>);
}

/// nav_msgs/msg/Odometry — pose + twist estimate.
#[repr(C)]
pub struct Odometry {
    pub header: Header,
    pub child_frame_id: rosidl_runtime_rs::String,
    pub pose: PoseWithCovariance,
    pub twist: TwistWithCovariance,
}

impl Default for Odometry {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !nav_msgs__msg__Odometry__init(&mut msg as *mut _) {
                panic!("Odometry__init failed");
            }
            msg
        }
    }
}

impl Clone for Odometry {
    fn clone(&self) -> Self {
        Self {
            header: self.header.clone(),
            child_frame_id: self.child_frame_id.clone(),
            pose: self.pose.clone(),
            twist: self.twist.clone(),
        }
    }
}

impl std::fmt::Debug for Odometry {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Odometry")
            .field("header", &self.header)
            .field("child_frame_id", &self.child_frame_id.to_cstr())
            .field("pose", &self.pose)
            .field("twist", &self.twist)
            .finish()
    }
}

impl Drop for Odometry {
    fn drop(&mut self) {
        unsafe {
            nav_msgs__msg__Odometry__fini(self as *mut _);
        }
    }
}

impl SequenceAlloc for Odometry {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { nav_msgs__msg__Odometry__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { nav_msgs__msg__Odometry__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for Odometry {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for Odometry
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "nav_msgs/msg/Odometry";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__nav_msgs__msg__Odometry()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__nav_msgs__msg__Odometry()
        }
    }
}

// Re-export helpers for convenience
pub use geometry_msgs_rs::{PoseWithCovariance as OdomPose, TwistWithCovariance as OdomTwist};
pub use sensor_msgs_rs::Header as OdomHeader;

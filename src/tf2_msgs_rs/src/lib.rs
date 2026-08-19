//! Rust bindings for tf2_msgs
//!
//! Provides tf2_msgs/msg/TFMessage message type.

use geometry_msgs_rs::TransformStamped;
use rosidl_runtime_rs::{Message, RmwMessage, Sequence, SequenceAlloc};

// ========================= tf2_msgs/msg/TFMessage =========================

#[link(name = "tf2_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn tf2_msgs__msg__TFMessage__init(msg: *mut TFMessage) -> bool;
    fn tf2_msgs__msg__TFMessage__fini(msg: *mut TFMessage);
    fn tf2_msgs__msg__TFMessage__Sequence__init(seq: *mut Sequence<TFMessage>, size: usize) -> bool;
    fn tf2_msgs__msg__TFMessage__Sequence__fini(seq: *mut Sequence<TFMessage>);
}

/// tf2_msgs/msg/TFMessage — array of transforms.
#[repr(C)]
pub struct TFMessage {
    pub transforms: Sequence<TransformStamped>,
}

impl Default for TFMessage {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !tf2_msgs__msg__TFMessage__init(&mut msg as *mut _) {
                panic!("TFMessage__init failed");
            }
            msg
        }
    }
}

impl Clone for TFMessage {
    fn clone(&self) -> Self {
        Self {
            transforms: self.transforms.clone(),
        }
    }
}

impl std::fmt::Debug for TFMessage {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("TFMessage")
            .field("transforms", &self.transforms)
            .finish()
    }
}

impl Drop for TFMessage {
    fn drop(&mut self) {
        unsafe {
            tf2_msgs__msg__TFMessage__fini(self as *mut _);
        }
    }
}

impl SequenceAlloc for TFMessage {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { tf2_msgs__msg__TFMessage__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { tf2_msgs__msg__TFMessage__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for TFMessage {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for TFMessage
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "tf2_msgs/msg/TFMessage";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__tf2_msgs__msg__TFMessage()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__tf2_msgs__msg__TFMessage()
        }
    }
}

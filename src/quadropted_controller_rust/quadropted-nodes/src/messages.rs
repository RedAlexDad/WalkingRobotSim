//! Custom message types for ROS 2 communication
//!
//! These types follow the pattern from rclrs vendor directory.
//! They link directly to the ROS 2 type support libraries.

use rosidl_runtime_rs::{Message, RmwMessage, Sequence, SequenceAlloc};

// ========================= std_msgs/msg/Float64MultiArray =========================

mod std_msgs_float64_multi_array {
    use super::*;

    #[link(name = "std_msgs__rosidl_typesupport_c")]
    unsafe extern "C" {
        fn rosidl_typesupport_c__get_message_type_support_handle__std_msgs__msg__Float64MultiArray()
            -> *const std::ffi::c_void;
    }

    #[link(name = "std_msgs__rosidl_generator_c")]
    unsafe extern "C" {
        fn std_msgs__msg__Float64MultiArray__init(msg: *mut Float64MultiArray) -> bool;
        fn std_msgs__msg__Float64MultiArray__Sequence__init(
            seq: *mut Sequence<Float64MultiArray>,
            size: usize,
        ) -> bool;
        fn std_msgs__msg__Float64MultiArray__Sequence__fini(seq: *mut Sequence<Float64MultiArray>);
        fn std_msgs__msg__Float64MultiArray__Sequence__copy(
            in_seq: &Sequence<Float64MultiArray>,
            out_seq: *mut Sequence<Float64MultiArray>,
        ) -> bool;
    }

    #[repr(C)]
    #[derive(Clone, Debug, PartialEq, PartialOrd)]
    pub struct Float64MultiArray {
        pub layout: MultiArrayLayout,
        pub data: Sequence<f64>,
    }

    #[repr(C)]
    #[derive(Clone, Debug, PartialEq, PartialOrd)]
    pub struct MultiArrayLayout {
        pub dim: Sequence<MultiArrayDimension>,
        pub data_offset: u32,
    }

    #[repr(C)]
    #[derive(Clone, Debug, PartialEq, PartialOrd)]
    pub struct MultiArrayDimension {
        pub label: rosidl_runtime_rs::String,
        pub size: u32,
        pub stride: u32,
    }

    impl Default for Float64MultiArray {
        fn default() -> Self {
            unsafe {
                let mut msg = std::mem::zeroed();
                if !std_msgs__msg__Float64MultiArray__init(&mut msg as *mut _) {
                    panic!("Call to Float64MultiArray__init() failed");
                }
                msg
            }
        }
    }

    impl Default for MultiArrayLayout {
        fn default() -> Self {
            Self {
                dim: Sequence::new(),
                data_offset: 0,
            }
        }
    }

    impl Default for MultiArrayDimension {
        fn default() -> Self {
            Self {
                label: rosidl_runtime_rs::String::from(""),
                size: 0,
                stride: 0,
            }
        }
    }

    impl SequenceAlloc for Float64MultiArray {
        fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
            unsafe { std_msgs__msg__Float64MultiArray__Sequence__init(seq as *mut _, size) }
        }
        fn sequence_fini(seq: &mut Sequence<Self>) {
            unsafe { std_msgs__msg__Float64MultiArray__Sequence__fini(seq as *mut _) }
        }
        fn sequence_copy(in_seq: &Sequence<Self>, out_seq: &mut Sequence<Self>) -> bool {
            unsafe { std_msgs__msg__Float64MultiArray__Sequence__copy(in_seq, out_seq as *mut _) }
        }
    }

    impl Message for Float64MultiArray {
        type RmwMsg = Self;
        fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
            msg_cow
        }
        fn from_rmw_message(msg: Self::RmwMsg) -> Self {
            msg
        }
    }

    impl RmwMessage for Float64MultiArray
    where
        Self: Sized,
    {
        const TYPE_NAME: &'static str = "std_msgs/msg/Float64MultiArray";
        fn get_type_support() -> *const std::ffi::c_void {
            unsafe { rosidl_typesupport_c__get_message_type_support_handle__std_msgs__msg__Float64MultiArray() }
        }
    }
}

// ========================= geometry_msgs/msg/Twist =========================

mod geometry_msgs_twist {
    use super::*;

    #[link(name = "geometry_msgs__rosidl_typesupport_c")]
    unsafe extern "C" {
        fn rosidl_typesupport_c__get_message_type_support_handle__geometry_msgs__msg__Twist()
            -> *const std::ffi::c_void;
    }

    #[link(name = "geometry_msgs__rosidl_generator_c")]
    unsafe extern "C" {
        fn geometry_msgs__msg__Twist__init(msg: *mut Twist) -> bool;
        fn geometry_msgs__msg__Twist__Sequence__init(
            seq: *mut Sequence<Twist>,
            size: usize,
        ) -> bool;
        fn geometry_msgs__msg__Twist__Sequence__fini(seq: *mut Sequence<Twist>);
        fn geometry_msgs__msg__Twist__Sequence__copy(
            in_seq: &Sequence<Twist>,
            out_seq: *mut Sequence<Twist>,
        ) -> bool;
    }

    #[repr(C)]
    #[derive(Clone, Debug, PartialEq, PartialOrd)]
    pub struct Twist {
        pub linear: Vector3,
        pub angular: Vector3,
    }

    #[repr(C)]
    #[derive(Clone, Debug, PartialEq, PartialOrd)]
    pub struct Vector3 {
        pub x: f64,
        pub y: f64,
        pub z: f64,
    }

    impl Default for Twist {
        fn default() -> Self {
            unsafe {
                let mut msg = std::mem::zeroed();
                if !geometry_msgs__msg__Twist__init(&mut msg as *mut _) {
                    panic!("Call to Twist__init() failed");
                }
                msg
            }
        }
    }

    impl Default for Vector3 {
        fn default() -> Self {
            Self { x: 0.0, y: 0.0, z: 0.0 }
        }
    }

    impl SequenceAlloc for Twist {
        fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
            unsafe { geometry_msgs__msg__Twist__Sequence__init(seq as *mut _, size) }
        }
        fn sequence_fini(seq: &mut Sequence<Self>) {
            unsafe { geometry_msgs__msg__Twist__Sequence__fini(seq as *mut _) }
        }
        fn sequence_copy(in_seq: &Sequence<Self>, out_seq: &mut Sequence<Self>) -> bool {
            unsafe { geometry_msgs__msg__Twist__Sequence__copy(in_seq, out_seq as *mut _) }
        }
    }

    impl Message for Twist {
        type RmwMsg = Self;
        fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
            msg_cow
        }
        fn from_rmw_message(msg: Self::RmwMsg) -> Self {
            msg
        }
    }

    impl RmwMessage for Twist
    where
        Self: Sized,
    {
        const TYPE_NAME: &'static str = "geometry_msgs/msg/Twist";
        fn get_type_support() -> *const std::ffi::c_void {
            unsafe { rosidl_typesupport_c__get_message_type_support_handle__geometry_msgs__msg__Twist() }
        }
    }
}

// ========================= Public exports =========================

pub use std_msgs_float64_multi_array::{Float64MultiArray, MultiArrayDimension, MultiArrayLayout};
pub use geometry_msgs_twist::{Twist, Vector3};

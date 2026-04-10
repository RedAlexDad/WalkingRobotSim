//! Rust bindings for geometry_msgs
//!
//! Uses rosidl_runtime_rs traits with manual linking via build.rs.

use rosidl_runtime_rs::{Message, RmwMessage, Sequence, SequenceAlloc};

// ========================= geometry_msgs/msg/Vector3 =========================

#[link(name = "geometry_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn geometry_msgs__msg__Vector3__init(msg: *mut Vector3) -> bool;
    fn geometry_msgs__msg__Vector3__Sequence__init(seq: *mut Sequence<Vector3>, size: usize) -> bool;
    fn geometry_msgs__msg__Vector3__Sequence__fini(seq: *mut Sequence<Vector3>);
}

#[repr(C)]
#[derive(Clone, Debug)]
pub struct Vector3 {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Default for Vector3 {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !geometry_msgs__msg__Vector3__init(&mut msg as *mut _) {
                panic!("Vector3__init failed");
            }
            msg
        }
    }
}

impl SequenceAlloc for Vector3 {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { geometry_msgs__msg__Vector3__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { geometry_msgs__msg__Vector3__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for Vector3 {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for Vector3
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "geometry_msgs/msg/Vector3";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            // Type support is in typesupport_c library
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__geometry_msgs__msg__Vector3()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__geometry_msgs__msg__Vector3()
        }
    }
}

// ========================= geometry_msgs/msg/Twist =========================

#[link(name = "geometry_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn geometry_msgs__msg__Twist__init(msg: *mut Twist) -> bool;
    fn geometry_msgs__msg__Twist__Sequence__init(seq: *mut Sequence<Twist>, size: usize) -> bool;
    fn geometry_msgs__msg__Twist__Sequence__fini(seq: *mut Sequence<Twist>);
}

#[repr(C)]
#[derive(Clone, Debug)]
pub struct Twist {
    pub linear: Vector3,
    pub angular: Vector3,
}

impl Default for Twist {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !geometry_msgs__msg__Twist__init(&mut msg as *mut _) {
                panic!("Twist__init failed");
            }
            msg
        }
    }
}

impl SequenceAlloc for Twist {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { geometry_msgs__msg__Twist__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { geometry_msgs__msg__Twist__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for Twist {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for Twist
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "geometry_msgs/msg/Twist";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__geometry_msgs__msg__Twist()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__geometry_msgs__msg__Twist()
        }
    }
}

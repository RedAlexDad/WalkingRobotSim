//! Rust bindings for std_msgs
//!
//! Uses rosidl_runtime_rs traits with manual linking via build.rs.

use rosidl_runtime_rs::{Message, RmwMessage, Sequence, SequenceAlloc};

// ========================= std_msgs/msg/MultiArrayLayout =========================

#[link(name = "std_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn std_msgs__msg__MultiArrayDimension__init(msg: *mut MultiArrayDimension) -> bool;
    fn std_msgs__msg__MultiArrayDimension__Sequence__init(seq: *mut Sequence<MultiArrayDimension>, size: usize) -> bool;
    fn std_msgs__msg__MultiArrayDimension__Sequence__fini(seq: *mut Sequence<MultiArrayDimension>);
    fn std_msgs__msg__MultiArrayLayout__init(msg: *mut MultiArrayLayout) -> bool;
}

#[repr(C)]
#[derive(Clone, Debug)]
pub struct MultiArrayDimension {
    pub label: rosidl_runtime_rs::String,
    pub size: u32,
    pub stride: u32,
}

impl Default for MultiArrayDimension {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !std_msgs__msg__MultiArrayDimension__init(&mut msg as *mut _) {
                panic!("MultiArrayDimension__init failed");
            }
            msg
        }
    }
}

impl SequenceAlloc for MultiArrayDimension {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { std_msgs__msg__MultiArrayDimension__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { std_msgs__msg__MultiArrayDimension__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

#[repr(C)]
#[derive(Clone, Debug)]
pub struct MultiArrayLayout {
    pub dim: Sequence<MultiArrayDimension>,
    pub data_offset: u32,
}

impl Default for MultiArrayLayout {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !std_msgs__msg__MultiArrayLayout__init(&mut msg as *mut _) {
                panic!("MultiArrayLayout__init failed");
            }
            msg
        }
    }
}

// ========================= std_msgs/msg/Float64MultiArray =========================

#[link(name = "std_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn std_msgs__msg__Float64MultiArray__init(msg: *mut Float64MultiArray) -> bool;
    fn std_msgs__msg__Float64MultiArray__Sequence__init(seq: *mut Sequence<Float64MultiArray>, size: usize) -> bool;
    fn std_msgs__msg__Float64MultiArray__Sequence__fini(seq: *mut Sequence<Float64MultiArray>);
}

#[repr(C)]
#[derive(Clone, Debug)]
pub struct Float64MultiArray {
    pub layout: MultiArrayLayout,
    pub data: Sequence<f64>,
}

impl Default for Float64MultiArray {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !std_msgs__msg__Float64MultiArray__init(&mut msg as *mut _) {
                panic!("Float64MultiArray__init failed");
            }
            msg
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
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for Float64MultiArray {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for Float64MultiArray
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "std_msgs/msg/Float64MultiArray";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__std_msgs__msg__Float64MultiArray()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__std_msgs__msg__Float64MultiArray()
        }
    }
}

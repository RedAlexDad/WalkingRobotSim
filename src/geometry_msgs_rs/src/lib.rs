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

// ========================= geometry_msgs/msg/Quaternion =========================

#[link(name = "geometry_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn geometry_msgs__msg__Quaternion__init(msg: *mut Quaternion) -> bool;
    fn geometry_msgs__msg__Quaternion__Sequence__init(seq: *mut Sequence<Quaternion>, size: usize) -> bool;
    fn geometry_msgs__msg__Quaternion__Sequence__fini(seq: *mut Sequence<Quaternion>);
}

#[repr(C)]
#[derive(Clone, Debug)]
pub struct Quaternion {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub w: f64,
}

impl Default for Quaternion {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !geometry_msgs__msg__Quaternion__init(&mut msg as *mut _) {
                panic!("Quaternion__init failed");
            }
            msg
        }
    }
}

impl SequenceAlloc for Quaternion {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { geometry_msgs__msg__Quaternion__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { geometry_msgs__msg__Quaternion__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for Quaternion {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for Quaternion
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "geometry_msgs/msg/Quaternion";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__geometry_msgs__msg__Quaternion()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__geometry_msgs__msg__Quaternion()
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

// ========================= geometry_msgs/msg/Point =========================

#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Point {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Point {
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z }
    }
}

// ========================= geometry_msgs/msg/Pose =========================

#[link(name = "geometry_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn geometry_msgs__msg__Pose__init(msg: *mut Pose) -> bool;
    fn geometry_msgs__msg__Pose__fini(msg: *mut Pose);
    fn geometry_msgs__msg__PoseWithCovariance__init(msg: *mut PoseWithCovariance) -> bool;
    fn geometry_msgs__msg__PoseWithCovariance__fini(msg: *mut PoseWithCovariance);
    fn geometry_msgs__msg__TwistWithCovariance__init(msg: *mut TwistWithCovariance) -> bool;
    fn geometry_msgs__msg__TwistWithCovariance__fini(msg: *mut TwistWithCovariance);
    fn geometry_msgs__msg__Transform__init(msg: *mut Transform) -> bool;
    fn geometry_msgs__msg__Transform__fini(msg: *mut Transform);
    fn geometry_msgs__msg__TransformStamped__init(msg: *mut TransformStamped) -> bool;
    fn geometry_msgs__msg__TransformStamped__fini(msg: *mut TransformStamped);
    fn geometry_msgs__msg__TransformStamped__Sequence__init(seq: *mut Sequence<TransformStamped>, size: usize) -> bool;
    fn geometry_msgs__msg__TransformStamped__Sequence__fini(seq: *mut Sequence<TransformStamped>);
}

/// geometry_msgs/msg/Pose
#[repr(C)]
#[derive(Clone, Debug)]
pub struct Pose {
    pub position: Point,
    pub orientation: Quaternion,
}

impl Default for Pose {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !geometry_msgs__msg__Pose__init(&mut msg as *mut _) {
                panic!("Pose__init failed");
            }
            msg
        }
    }
}

impl Drop for Pose {
    fn drop(&mut self) {
        unsafe {
            geometry_msgs__msg__Pose__fini(self as *mut _);
        }
    }
}

// ========================= geometry_msgs/msg/PoseWithCovariance =========================

/// geometry_msgs/msg/PoseWithCovariance
#[repr(C)]
#[derive(Clone, Debug)]
pub struct PoseWithCovariance {
    pub pose: Pose,
    pub covariance: [f64; 36],
}

impl Default for PoseWithCovariance {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !geometry_msgs__msg__PoseWithCovariance__init(&mut msg as *mut _) {
                panic!("PoseWithCovariance__init failed");
            }
            msg
        }
    }
}

impl Drop for PoseWithCovariance {
    fn drop(&mut self) {
        unsafe {
            geometry_msgs__msg__PoseWithCovariance__fini(self as *mut _);
        }
    }
}

// ========================= geometry_msgs/msg/TwistWithCovariance =========================

/// geometry_msgs/msg/TwistWithCovariance
#[repr(C)]
#[derive(Clone, Debug)]
pub struct TwistWithCovariance {
    pub twist: Twist,
    pub covariance: [f64; 36],
}

impl Default for TwistWithCovariance {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !geometry_msgs__msg__TwistWithCovariance__init(&mut msg as *mut _) {
                panic!("TwistWithCovariance__init failed");
            }
            msg
        }
    }
}

impl Drop for TwistWithCovariance {
    fn drop(&mut self) {
        unsafe {
            geometry_msgs__msg__TwistWithCovariance__fini(self as *mut _);
        }
    }
}

// ========================= geometry_msgs/msg/Transform =========================

/// geometry_msgs/msg/Transform
#[repr(C)]
#[derive(Clone, Debug)]
pub struct Transform {
    pub translation: Vector3,
    pub rotation: Quaternion,
}

impl Default for Transform {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !geometry_msgs__msg__Transform__init(&mut msg as *mut _) {
                panic!("Transform__init failed");
            }
            msg
        }
    }
}

impl Drop for Transform {
    fn drop(&mut self) {
        unsafe {
            geometry_msgs__msg__Transform__fini(self as *mut _);
        }
    }
}

// ========================= std_msgs/msg/Header (replica) =========================

/// std_msgs/msg/Header — C-compatible replica (same layout as sensor_msgs_rs::Header).
#[repr(C)]
pub struct Header {
    pub stamp: Time,
    pub frame_id: rosidl_runtime_rs::String,
}

/// builtin_interfaces/msg/Time
#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct Time {
    pub sec: i32,
    pub nanosec: u32,
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

// ========================= geometry_msgs/msg/TransformStamped =========================

/// geometry_msgs/msg/TransformStamped
#[repr(C)]
pub struct TransformStamped {
    pub header: Header,
    pub child_frame_id: rosidl_runtime_rs::String,
    pub transform: Transform,
}

impl Default for TransformStamped {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !geometry_msgs__msg__TransformStamped__init(&mut msg as *mut _) {
                panic!("TransformStamped__init failed");
            }
            msg
        }
    }
}

impl Clone for TransformStamped {
    fn clone(&self) -> Self {
        Self {
            header: self.header.clone(),
            child_frame_id: self.child_frame_id.clone(),
            transform: self.transform.clone(),
        }
    }
}

impl std::fmt::Debug for TransformStamped {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("TransformStamped")
            .field("header", &self.header)
            .field("child_frame_id", &self.child_frame_id.to_cstr())
            .field("transform", &self.transform)
            .finish()
    }
}

impl Drop for TransformStamped {
    fn drop(&mut self) {
        unsafe {
            geometry_msgs__msg__TransformStamped__fini(self as *mut _);
        }
    }
}

impl SequenceAlloc for TransformStamped {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { geometry_msgs__msg__TransformStamped__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { geometry_msgs__msg__TransformStamped__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

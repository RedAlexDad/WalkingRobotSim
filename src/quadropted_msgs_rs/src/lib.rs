//! Rust bindings for quadropted_msgs
//!
//! Provides RobotModeCommand and RobotVelocity message types.

use rosidl_runtime_rs::{Message, RmwMessage, Sequence, SequenceAlloc};
use geometry_msgs_rs::Twist;

// ========================= quadropted_msgs/msg/RobotModeCommand =========================

#[link(name = "quadropted_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn quadropted_msgs__msg__RobotModeCommand__init(msg: *mut RobotModeCommand) -> bool;
    fn quadropted_msgs__msg__RobotModeCommand__fini(msg: *mut RobotModeCommand);
    fn quadropted_msgs__msg__RobotModeCommand__Sequence__init(seq: *mut Sequence<RobotModeCommand>, size: usize) -> bool;
    fn quadropted_msgs__msg__RobotModeCommand__Sequence__fini(seq: *mut Sequence<RobotModeCommand>);
}

#[repr(C)]
pub struct RobotModeCommand {
    pub mode: rosidl_runtime_rs::String,
    pub robot_id: u16,
}

impl Default for RobotModeCommand {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !quadropted_msgs__msg__RobotModeCommand__init(&mut msg as *mut _) {
                panic!("RobotModeCommand__init failed");
            }
            msg
        }
    }
}

impl Clone for RobotModeCommand {
    fn clone(&self) -> Self {
        Self {
            mode: self.mode.clone(),
            robot_id: self.robot_id,
        }
    }
}

impl std::fmt::Debug for RobotModeCommand {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("RobotModeCommand")
            .field("mode", &self.mode.to_cstr())
            .field("robot_id", &self.robot_id)
            .finish()
    }
}

impl Drop for RobotModeCommand {
    fn drop(&mut self) {
        unsafe {
            quadropted_msgs__msg__RobotModeCommand__fini(self as *mut _);
        }
    }
}

impl SequenceAlloc for RobotModeCommand {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { quadropted_msgs__msg__RobotModeCommand__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { quadropted_msgs__msg__RobotModeCommand__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for RobotModeCommand {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for RobotModeCommand
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "quadropted_msgs/msg/RobotModeCommand";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__msg__RobotModeCommand()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__msg__RobotModeCommand()
        }
    }
}

// ========================= quadropted_msgs/msg/RobotVelocity =========================

#[link(name = "quadropted_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn quadropted_msgs__msg__RobotVelocity__init(msg: *mut RobotVelocity) -> bool;
    fn quadropted_msgs__msg__RobotVelocity__fini(msg: *mut RobotVelocity);
    fn quadropted_msgs__msg__RobotVelocity__Sequence__init(seq: *mut Sequence<RobotVelocity>, size: usize) -> bool;
    fn quadropted_msgs__msg__RobotVelocity__Sequence__fini(seq: *mut Sequence<RobotVelocity>);
}

#[repr(C)]
pub struct RobotVelocity {
    pub robot_id: u16,
    pub cmd_vel: Twist,
}

impl Default for RobotVelocity {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !quadropted_msgs__msg__RobotVelocity__init(&mut msg as *mut _) {
                panic!("RobotVelocity__init failed");
            }
            msg
        }
    }
}

impl Clone for RobotVelocity {
    fn clone(&self) -> Self {
        Self {
            robot_id: self.robot_id,
            cmd_vel: self.cmd_vel.clone(),
        }
    }
}

impl std::fmt::Debug for RobotVelocity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("RobotVelocity")
            .field("robot_id", &self.robot_id)
            .field("cmd_vel", &self.cmd_vel)
            .finish()
    }
}

impl Drop for RobotVelocity {
    fn drop(&mut self) {
        unsafe {
            quadropted_msgs__msg__RobotVelocity__fini(self as *mut _);
        }
    }
}

impl SequenceAlloc for RobotVelocity {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { quadropted_msgs__msg__RobotVelocity__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { quadropted_msgs__msg__RobotVelocity__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for RobotVelocity {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for RobotVelocity
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "quadropted_msgs/msg/RobotVelocity";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__msg__RobotVelocity()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__msg__RobotVelocity()
        }
    }
}

// ========================= quadropted_msgs/msg/RobotFootContact =========================

#[link(name = "quadropted_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn quadropted_msgs__msg__RobotFootContact__init(msg: *mut RobotFootContact) -> bool;
    fn quadropted_msgs__msg__RobotFootContact__fini(msg: *mut RobotFootContact);
    fn quadropted_msgs__msg__RobotFootContact__Sequence__init(seq: *mut Sequence<RobotFootContact>, size: usize) -> bool;
    fn quadropted_msgs__msg__RobotFootContact__Sequence__fini(seq: *mut Sequence<RobotFootContact>);
}

/// Robot foot contact message: `bool[4] contacts` — [FR, FL, RR, RL].
#[repr(C)]
#[derive(Clone, Debug)]
pub struct RobotFootContact {
    pub contacts: [bool; 4],
}

impl Default for RobotFootContact {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !quadropted_msgs__msg__RobotFootContact__init(&mut msg as *mut _) {
                panic!("RobotFootContact__init failed");
            }
            msg
        }
    }
}

impl SequenceAlloc for RobotFootContact {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { quadropted_msgs__msg__RobotFootContact__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { quadropted_msgs__msg__RobotFootContact__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for RobotFootContact {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for RobotFootContact
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "quadropted_msgs/msg/RobotFootContact";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__msg__RobotFootContact()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__msg__RobotFootContact()
        }
    }
}

// ========================= quadropted_msgs/srv/RobotBehaviorCommand =========================

#[link(name = "quadropted_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn quadropted_msgs__srv__RobotBehaviorCommand_Request__init(msg: *mut RobotBehaviorCommand_Request) -> bool;
    fn quadropted_msgs__srv__RobotBehaviorCommand_Request__fini(msg: *mut RobotBehaviorCommand_Request);
    fn quadropted_msgs__srv__RobotBehaviorCommand_Response__init(msg: *mut RobotBehaviorCommand_Response) -> bool;
    fn quadropted_msgs__srv__RobotBehaviorCommand_Response__fini(msg: *mut RobotBehaviorCommand_Response);
}

/// RobotBehaviorCommand_Request — string command (sit/up/walk)
#[repr(C)]
pub struct RobotBehaviorCommand_Request {
    pub command: rosidl_runtime_rs::String,
}

impl Default for RobotBehaviorCommand_Request {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !quadropted_msgs__srv__RobotBehaviorCommand_Request__init(&mut msg as *mut _) {
                panic!("RobotBehaviorCommand_Request__init failed");
            }
            msg
        }
    }
}

impl Clone for RobotBehaviorCommand_Request {
    fn clone(&self) -> Self {
        Self {
            command: self.command.clone(),
        }
    }
}

impl std::fmt::Debug for RobotBehaviorCommand_Request {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("RobotBehaviorCommand_Request")
            .field("command", &self.command.to_cstr())
            .finish()
    }
}

impl Drop for RobotBehaviorCommand_Request {
    fn drop(&mut self) {
        unsafe {
            quadropted_msgs__srv__RobotBehaviorCommand_Request__fini(self as *mut _);
        }
    }
}

impl rosidl_runtime_rs::Message for RobotBehaviorCommand_Request {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RobotBehaviorCommand_Request {
    const TYPE_NAME: &'static str = "quadropted_msgs/srv/RobotBehaviorCommand_Request";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__srv__RobotBehaviorCommand_Request()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__srv__RobotBehaviorCommand_Request()
        }
    }
}

/// RobotBehaviorCommand_Response — success bool + message string
#[repr(C)]
pub struct RobotBehaviorCommand_Response {
    pub success: bool,
    pub message: rosidl_runtime_rs::String,
}

impl Default for RobotBehaviorCommand_Response {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !quadropted_msgs__srv__RobotBehaviorCommand_Response__init(&mut msg as *mut _) {
                panic!("RobotBehaviorCommand_Response__init failed");
            }
            msg
        }
    }
}

impl Clone for RobotBehaviorCommand_Response {
    fn clone(&self) -> Self {
        Self {
            success: self.success,
            message: self.message.clone(),
        }
    }
}

impl std::fmt::Debug for RobotBehaviorCommand_Response {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("RobotBehaviorCommand_Response")
            .field("success", &self.success)
            .field("message", &self.message.to_cstr())
            .finish()
    }
}

impl Drop for RobotBehaviorCommand_Response {
    fn drop(&mut self) {
        unsafe {
            quadropted_msgs__srv__RobotBehaviorCommand_Response__fini(self as *mut _);
        }
    }
}

impl rosidl_runtime_rs::Message for RobotBehaviorCommand_Response {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RobotBehaviorCommand_Response {
    const TYPE_NAME: &'static str = "quadropted_msgs/srv/RobotBehaviorCommand_Response";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__srv__RobotBehaviorCommand_Response()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__quadropted_msgs__srv__RobotBehaviorCommand_Response()
        }
    }
}

/// RobotBehaviorCommand service marker type
pub struct RobotBehaviorCommand;

impl rosidl_runtime_rs::Service for RobotBehaviorCommand {
    type Request = RobotBehaviorCommand_Request;
    type Response = RobotBehaviorCommand_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_service_type_support_handle__quadropted_msgs__srv__RobotBehaviorCommand()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_service_type_support_handle__quadropted_msgs__srv__RobotBehaviorCommand()
        }
    }
}

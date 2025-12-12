// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from ros2_unitree_legged_msgs:msg/HighState.idl
// generated code does not contain a copyright notice
#include "ros2_unitree_legged_msgs/msg/detail/high_state__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <cstddef>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "ros2_unitree_legged_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "ros2_unitree_legged_msgs/msg/detail/high_state__struct.h"
#include "ros2_unitree_legged_msgs/msg/detail/high_state__functions.h"
#include "fastcdr/Cdr.h"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif

#include "ros2_unitree_legged_msgs/msg/detail/bms_state__functions.h"  // bms
#include "ros2_unitree_legged_msgs/msg/detail/cartesian__functions.h"  // foot_position2body, foot_speed2body
#include "ros2_unitree_legged_msgs/msg/detail/imu__functions.h"  // imu
#include "ros2_unitree_legged_msgs/msg/detail/motor_state__functions.h"  // motor_state

// forward declare type support functions

bool cdr_serialize_ros2_unitree_legged_msgs__msg__BmsState(
  const ros2_unitree_legged_msgs__msg__BmsState * ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool cdr_deserialize_ros2_unitree_legged_msgs__msg__BmsState(
  eprosima::fastcdr::Cdr & cdr,
  ros2_unitree_legged_msgs__msg__BmsState * ros_message);

size_t get_serialized_size_ros2_unitree_legged_msgs__msg__BmsState(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_ros2_unitree_legged_msgs__msg__BmsState(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

bool cdr_serialize_key_ros2_unitree_legged_msgs__msg__BmsState(
  const ros2_unitree_legged_msgs__msg__BmsState * ros_message,
  eprosima::fastcdr::Cdr & cdr);

size_t get_serialized_size_key_ros2_unitree_legged_msgs__msg__BmsState(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_key_ros2_unitree_legged_msgs__msg__BmsState(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, ros2_unitree_legged_msgs, msg, BmsState)();

bool cdr_serialize_ros2_unitree_legged_msgs__msg__Cartesian(
  const ros2_unitree_legged_msgs__msg__Cartesian * ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool cdr_deserialize_ros2_unitree_legged_msgs__msg__Cartesian(
  eprosima::fastcdr::Cdr & cdr,
  ros2_unitree_legged_msgs__msg__Cartesian * ros_message);

size_t get_serialized_size_ros2_unitree_legged_msgs__msg__Cartesian(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_ros2_unitree_legged_msgs__msg__Cartesian(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

bool cdr_serialize_key_ros2_unitree_legged_msgs__msg__Cartesian(
  const ros2_unitree_legged_msgs__msg__Cartesian * ros_message,
  eprosima::fastcdr::Cdr & cdr);

size_t get_serialized_size_key_ros2_unitree_legged_msgs__msg__Cartesian(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_key_ros2_unitree_legged_msgs__msg__Cartesian(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, ros2_unitree_legged_msgs, msg, Cartesian)();

bool cdr_serialize_ros2_unitree_legged_msgs__msg__IMU(
  const ros2_unitree_legged_msgs__msg__IMU * ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool cdr_deserialize_ros2_unitree_legged_msgs__msg__IMU(
  eprosima::fastcdr::Cdr & cdr,
  ros2_unitree_legged_msgs__msg__IMU * ros_message);

size_t get_serialized_size_ros2_unitree_legged_msgs__msg__IMU(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_ros2_unitree_legged_msgs__msg__IMU(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

bool cdr_serialize_key_ros2_unitree_legged_msgs__msg__IMU(
  const ros2_unitree_legged_msgs__msg__IMU * ros_message,
  eprosima::fastcdr::Cdr & cdr);

size_t get_serialized_size_key_ros2_unitree_legged_msgs__msg__IMU(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_key_ros2_unitree_legged_msgs__msg__IMU(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, ros2_unitree_legged_msgs, msg, IMU)();

bool cdr_serialize_ros2_unitree_legged_msgs__msg__MotorState(
  const ros2_unitree_legged_msgs__msg__MotorState * ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool cdr_deserialize_ros2_unitree_legged_msgs__msg__MotorState(
  eprosima::fastcdr::Cdr & cdr,
  ros2_unitree_legged_msgs__msg__MotorState * ros_message);

size_t get_serialized_size_ros2_unitree_legged_msgs__msg__MotorState(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_ros2_unitree_legged_msgs__msg__MotorState(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

bool cdr_serialize_key_ros2_unitree_legged_msgs__msg__MotorState(
  const ros2_unitree_legged_msgs__msg__MotorState * ros_message,
  eprosima::fastcdr::Cdr & cdr);

size_t get_serialized_size_key_ros2_unitree_legged_msgs__msg__MotorState(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_key_ros2_unitree_legged_msgs__msg__MotorState(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, ros2_unitree_legged_msgs, msg, MotorState)();


using _HighState__ros_msg_type = ros2_unitree_legged_msgs__msg__HighState;


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ros2_unitree_legged_msgs
bool cdr_serialize_ros2_unitree_legged_msgs__msg__HighState(
  const ros2_unitree_legged_msgs__msg__HighState * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: head
  {
    size_t size = 2;
    auto array_ptr = ros_message->head;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: level_flag
  {
    cdr << ros_message->level_flag;
  }

  // Field name: frame_reserve
  {
    cdr << ros_message->frame_reserve;
  }

  // Field name: sn
  {
    size_t size = 2;
    auto array_ptr = ros_message->sn;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: version
  {
    size_t size = 2;
    auto array_ptr = ros_message->version;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: band_width
  {
    cdr << ros_message->band_width;
  }

  // Field name: imu
  {
    cdr_serialize_ros2_unitree_legged_msgs__msg__IMU(
      &ros_message->imu, cdr);
  }

  // Field name: motor_state
  {
    size_t size = 20;
    auto array_ptr = ros_message->motor_state;
    for (size_t i = 0; i < size; ++i) {
      cdr_serialize_ros2_unitree_legged_msgs__msg__MotorState(
        &array_ptr[i], cdr);
    }
  }

  // Field name: bms
  {
    cdr_serialize_ros2_unitree_legged_msgs__msg__BmsState(
      &ros_message->bms, cdr);
  }

  // Field name: foot_force
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_force;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: foot_force_est
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_force_est;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: mode
  {
    cdr << ros_message->mode;
  }

  // Field name: progress
  {
    cdr << ros_message->progress;
  }

  // Field name: gait_type
  {
    cdr << ros_message->gait_type;
  }

  // Field name: foot_raise_height
  {
    cdr << ros_message->foot_raise_height;
  }

  // Field name: position
  {
    size_t size = 3;
    auto array_ptr = ros_message->position;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: body_height
  {
    cdr << ros_message->body_height;
  }

  // Field name: velocity
  {
    size_t size = 3;
    auto array_ptr = ros_message->velocity;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: yaw_speed
  {
    cdr << ros_message->yaw_speed;
  }

  // Field name: range_obstacle
  {
    size_t size = 4;
    auto array_ptr = ros_message->range_obstacle;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: foot_position2body
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_position2body;
    for (size_t i = 0; i < size; ++i) {
      cdr_serialize_ros2_unitree_legged_msgs__msg__Cartesian(
        &array_ptr[i], cdr);
    }
  }

  // Field name: foot_speed2body
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_speed2body;
    for (size_t i = 0; i < size; ++i) {
      cdr_serialize_ros2_unitree_legged_msgs__msg__Cartesian(
        &array_ptr[i], cdr);
    }
  }

  // Field name: wireless_remote
  {
    size_t size = 40;
    auto array_ptr = ros_message->wireless_remote;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: reserve
  {
    cdr << ros_message->reserve;
  }

  // Field name: crc
  {
    cdr << ros_message->crc;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ros2_unitree_legged_msgs
bool cdr_deserialize_ros2_unitree_legged_msgs__msg__HighState(
  eprosima::fastcdr::Cdr & cdr,
  ros2_unitree_legged_msgs__msg__HighState * ros_message)
{
  // Field name: head
  {
    size_t size = 2;
    auto array_ptr = ros_message->head;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: level_flag
  {
    cdr >> ros_message->level_flag;
  }

  // Field name: frame_reserve
  {
    cdr >> ros_message->frame_reserve;
  }

  // Field name: sn
  {
    size_t size = 2;
    auto array_ptr = ros_message->sn;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: version
  {
    size_t size = 2;
    auto array_ptr = ros_message->version;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: band_width
  {
    cdr >> ros_message->band_width;
  }

  // Field name: imu
  {
    cdr_deserialize_ros2_unitree_legged_msgs__msg__IMU(cdr, &ros_message->imu);
  }

  // Field name: motor_state
  {
    size_t size = 20;
    auto array_ptr = ros_message->motor_state;
    for (size_t i = 0; i < size; ++i) {
      cdr_deserialize_ros2_unitree_legged_msgs__msg__MotorState(cdr, &array_ptr[i]);
    }
  }

  // Field name: bms
  {
    cdr_deserialize_ros2_unitree_legged_msgs__msg__BmsState(cdr, &ros_message->bms);
  }

  // Field name: foot_force
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_force;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: foot_force_est
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_force_est;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: mode
  {
    cdr >> ros_message->mode;
  }

  // Field name: progress
  {
    cdr >> ros_message->progress;
  }

  // Field name: gait_type
  {
    cdr >> ros_message->gait_type;
  }

  // Field name: foot_raise_height
  {
    cdr >> ros_message->foot_raise_height;
  }

  // Field name: position
  {
    size_t size = 3;
    auto array_ptr = ros_message->position;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: body_height
  {
    cdr >> ros_message->body_height;
  }

  // Field name: velocity
  {
    size_t size = 3;
    auto array_ptr = ros_message->velocity;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: yaw_speed
  {
    cdr >> ros_message->yaw_speed;
  }

  // Field name: range_obstacle
  {
    size_t size = 4;
    auto array_ptr = ros_message->range_obstacle;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: foot_position2body
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_position2body;
    for (size_t i = 0; i < size; ++i) {
      cdr_deserialize_ros2_unitree_legged_msgs__msg__Cartesian(cdr, &array_ptr[i]);
    }
  }

  // Field name: foot_speed2body
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_speed2body;
    for (size_t i = 0; i < size; ++i) {
      cdr_deserialize_ros2_unitree_legged_msgs__msg__Cartesian(cdr, &array_ptr[i]);
    }
  }

  // Field name: wireless_remote
  {
    size_t size = 40;
    auto array_ptr = ros_message->wireless_remote;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: reserve
  {
    cdr >> ros_message->reserve;
  }

  // Field name: crc
  {
    cdr >> ros_message->crc;
  }

  return true;
}  // NOLINT(readability/fn_size)


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ros2_unitree_legged_msgs
size_t get_serialized_size_ros2_unitree_legged_msgs__msg__HighState(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _HighState__ros_msg_type * ros_message = static_cast<const _HighState__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: head
  {
    size_t array_size = 2;
    auto array_ptr = ros_message->head;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: level_flag
  {
    size_t item_size = sizeof(ros_message->level_flag);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: frame_reserve
  {
    size_t item_size = sizeof(ros_message->frame_reserve);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: sn
  {
    size_t array_size = 2;
    auto array_ptr = ros_message->sn;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: version
  {
    size_t array_size = 2;
    auto array_ptr = ros_message->version;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: band_width
  {
    size_t item_size = sizeof(ros_message->band_width);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: imu
  current_alignment += get_serialized_size_ros2_unitree_legged_msgs__msg__IMU(
    &(ros_message->imu), current_alignment);

  // Field name: motor_state
  {
    size_t array_size = 20;
    auto array_ptr = ros_message->motor_state;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += get_serialized_size_ros2_unitree_legged_msgs__msg__MotorState(
        &array_ptr[index], current_alignment);
    }
  }

  // Field name: bms
  current_alignment += get_serialized_size_ros2_unitree_legged_msgs__msg__BmsState(
    &(ros_message->bms), current_alignment);

  // Field name: foot_force
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->foot_force;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: foot_force_est
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->foot_force_est;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: mode
  {
    size_t item_size = sizeof(ros_message->mode);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: progress
  {
    size_t item_size = sizeof(ros_message->progress);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: gait_type
  {
    size_t item_size = sizeof(ros_message->gait_type);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: foot_raise_height
  {
    size_t item_size = sizeof(ros_message->foot_raise_height);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: position
  {
    size_t array_size = 3;
    auto array_ptr = ros_message->position;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: body_height
  {
    size_t item_size = sizeof(ros_message->body_height);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: velocity
  {
    size_t array_size = 3;
    auto array_ptr = ros_message->velocity;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: yaw_speed
  {
    size_t item_size = sizeof(ros_message->yaw_speed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: range_obstacle
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->range_obstacle;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: foot_position2body
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->foot_position2body;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += get_serialized_size_ros2_unitree_legged_msgs__msg__Cartesian(
        &array_ptr[index], current_alignment);
    }
  }

  // Field name: foot_speed2body
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->foot_speed2body;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += get_serialized_size_ros2_unitree_legged_msgs__msg__Cartesian(
        &array_ptr[index], current_alignment);
    }
  }

  // Field name: wireless_remote
  {
    size_t array_size = 40;
    auto array_ptr = ros_message->wireless_remote;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: reserve
  {
    size_t item_size = sizeof(ros_message->reserve);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: crc
  {
    size_t item_size = sizeof(ros_message->crc);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ros2_unitree_legged_msgs
size_t max_serialized_size_ros2_unitree_legged_msgs__msg__HighState(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;

  // Field name: head
  {
    size_t array_size = 2;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: level_flag
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: frame_reserve
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: sn
  {
    size_t array_size = 2;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: version
  {
    size_t array_size = 2;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: band_width
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: imu
  {
    size_t array_size = 1;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_ros2_unitree_legged_msgs__msg__IMU(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: motor_state
  {
    size_t array_size = 20;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_ros2_unitree_legged_msgs__msg__MotorState(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: bms
  {
    size_t array_size = 1;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_ros2_unitree_legged_msgs__msg__BmsState(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: foot_force
  {
    size_t array_size = 4;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: foot_force_est
  {
    size_t array_size = 4;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: mode
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: progress
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: gait_type
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: foot_raise_height
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: position
  {
    size_t array_size = 3;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: body_height
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: velocity
  {
    size_t array_size = 3;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: yaw_speed
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: range_obstacle
  {
    size_t array_size = 4;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: foot_position2body
  {
    size_t array_size = 4;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_ros2_unitree_legged_msgs__msg__Cartesian(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: foot_speed2body
  {
    size_t array_size = 4;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_ros2_unitree_legged_msgs__msg__Cartesian(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: wireless_remote
  {
    size_t array_size = 40;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: reserve
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: crc
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }


  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = ros2_unitree_legged_msgs__msg__HighState;
    is_plain =
      (
      offsetof(DataType, crc) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ros2_unitree_legged_msgs
bool cdr_serialize_key_ros2_unitree_legged_msgs__msg__HighState(
  const ros2_unitree_legged_msgs__msg__HighState * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: head
  {
    size_t size = 2;
    auto array_ptr = ros_message->head;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: level_flag
  {
    cdr << ros_message->level_flag;
  }

  // Field name: frame_reserve
  {
    cdr << ros_message->frame_reserve;
  }

  // Field name: sn
  {
    size_t size = 2;
    auto array_ptr = ros_message->sn;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: version
  {
    size_t size = 2;
    auto array_ptr = ros_message->version;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: band_width
  {
    cdr << ros_message->band_width;
  }

  // Field name: imu
  {
    cdr_serialize_key_ros2_unitree_legged_msgs__msg__IMU(
      &ros_message->imu, cdr);
  }

  // Field name: motor_state
  {
    size_t size = 20;
    auto array_ptr = ros_message->motor_state;
    for (size_t i = 0; i < size; ++i) {
      cdr_serialize_key_ros2_unitree_legged_msgs__msg__MotorState(
        &array_ptr[i], cdr);
    }
  }

  // Field name: bms
  {
    cdr_serialize_key_ros2_unitree_legged_msgs__msg__BmsState(
      &ros_message->bms, cdr);
  }

  // Field name: foot_force
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_force;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: foot_force_est
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_force_est;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: mode
  {
    cdr << ros_message->mode;
  }

  // Field name: progress
  {
    cdr << ros_message->progress;
  }

  // Field name: gait_type
  {
    cdr << ros_message->gait_type;
  }

  // Field name: foot_raise_height
  {
    cdr << ros_message->foot_raise_height;
  }

  // Field name: position
  {
    size_t size = 3;
    auto array_ptr = ros_message->position;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: body_height
  {
    cdr << ros_message->body_height;
  }

  // Field name: velocity
  {
    size_t size = 3;
    auto array_ptr = ros_message->velocity;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: yaw_speed
  {
    cdr << ros_message->yaw_speed;
  }

  // Field name: range_obstacle
  {
    size_t size = 4;
    auto array_ptr = ros_message->range_obstacle;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: foot_position2body
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_position2body;
    for (size_t i = 0; i < size; ++i) {
      cdr_serialize_key_ros2_unitree_legged_msgs__msg__Cartesian(
        &array_ptr[i], cdr);
    }
  }

  // Field name: foot_speed2body
  {
    size_t size = 4;
    auto array_ptr = ros_message->foot_speed2body;
    for (size_t i = 0; i < size; ++i) {
      cdr_serialize_key_ros2_unitree_legged_msgs__msg__Cartesian(
        &array_ptr[i], cdr);
    }
  }

  // Field name: wireless_remote
  {
    size_t size = 40;
    auto array_ptr = ros_message->wireless_remote;
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: reserve
  {
    cdr << ros_message->reserve;
  }

  // Field name: crc
  {
    cdr << ros_message->crc;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ros2_unitree_legged_msgs
size_t get_serialized_size_key_ros2_unitree_legged_msgs__msg__HighState(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _HighState__ros_msg_type * ros_message = static_cast<const _HighState__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;

  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: head
  {
    size_t array_size = 2;
    auto array_ptr = ros_message->head;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: level_flag
  {
    size_t item_size = sizeof(ros_message->level_flag);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: frame_reserve
  {
    size_t item_size = sizeof(ros_message->frame_reserve);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: sn
  {
    size_t array_size = 2;
    auto array_ptr = ros_message->sn;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: version
  {
    size_t array_size = 2;
    auto array_ptr = ros_message->version;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: band_width
  {
    size_t item_size = sizeof(ros_message->band_width);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: imu
  current_alignment += get_serialized_size_key_ros2_unitree_legged_msgs__msg__IMU(
    &(ros_message->imu), current_alignment);

  // Field name: motor_state
  {
    size_t array_size = 20;
    auto array_ptr = ros_message->motor_state;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += get_serialized_size_key_ros2_unitree_legged_msgs__msg__MotorState(
        &array_ptr[index], current_alignment);
    }
  }

  // Field name: bms
  current_alignment += get_serialized_size_key_ros2_unitree_legged_msgs__msg__BmsState(
    &(ros_message->bms), current_alignment);

  // Field name: foot_force
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->foot_force;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: foot_force_est
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->foot_force_est;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: mode
  {
    size_t item_size = sizeof(ros_message->mode);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: progress
  {
    size_t item_size = sizeof(ros_message->progress);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: gait_type
  {
    size_t item_size = sizeof(ros_message->gait_type);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: foot_raise_height
  {
    size_t item_size = sizeof(ros_message->foot_raise_height);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: position
  {
    size_t array_size = 3;
    auto array_ptr = ros_message->position;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: body_height
  {
    size_t item_size = sizeof(ros_message->body_height);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: velocity
  {
    size_t array_size = 3;
    auto array_ptr = ros_message->velocity;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: yaw_speed
  {
    size_t item_size = sizeof(ros_message->yaw_speed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: range_obstacle
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->range_obstacle;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: foot_position2body
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->foot_position2body;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += get_serialized_size_key_ros2_unitree_legged_msgs__msg__Cartesian(
        &array_ptr[index], current_alignment);
    }
  }

  // Field name: foot_speed2body
  {
    size_t array_size = 4;
    auto array_ptr = ros_message->foot_speed2body;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += get_serialized_size_key_ros2_unitree_legged_msgs__msg__Cartesian(
        &array_ptr[index], current_alignment);
    }
  }

  // Field name: wireless_remote
  {
    size_t array_size = 40;
    auto array_ptr = ros_message->wireless_remote;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: reserve
  {
    size_t item_size = sizeof(ros_message->reserve);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: crc
  {
    size_t item_size = sizeof(ros_message->crc);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ros2_unitree_legged_msgs
size_t max_serialized_size_key_ros2_unitree_legged_msgs__msg__HighState(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;
  // Field name: head
  {
    size_t array_size = 2;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: level_flag
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: frame_reserve
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: sn
  {
    size_t array_size = 2;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: version
  {
    size_t array_size = 2;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: band_width
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: imu
  {
    size_t array_size = 1;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_key_ros2_unitree_legged_msgs__msg__IMU(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: motor_state
  {
    size_t array_size = 20;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_key_ros2_unitree_legged_msgs__msg__MotorState(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: bms
  {
    size_t array_size = 1;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_key_ros2_unitree_legged_msgs__msg__BmsState(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: foot_force
  {
    size_t array_size = 4;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: foot_force_est
  {
    size_t array_size = 4;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: mode
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: progress
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: gait_type
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: foot_raise_height
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: position
  {
    size_t array_size = 3;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: body_height
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: velocity
  {
    size_t array_size = 3;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: yaw_speed
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: range_obstacle
  {
    size_t array_size = 4;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: foot_position2body
  {
    size_t array_size = 4;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_key_ros2_unitree_legged_msgs__msg__Cartesian(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: foot_speed2body
  {
    size_t array_size = 4;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_key_ros2_unitree_legged_msgs__msg__Cartesian(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: wireless_remote
  {
    size_t array_size = 40;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: reserve
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: crc
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = ros2_unitree_legged_msgs__msg__HighState;
    is_plain =
      (
      offsetof(DataType, crc) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}


static bool _HighState__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const ros2_unitree_legged_msgs__msg__HighState * ros_message = static_cast<const ros2_unitree_legged_msgs__msg__HighState *>(untyped_ros_message);
  (void)ros_message;
  return cdr_serialize_ros2_unitree_legged_msgs__msg__HighState(ros_message, cdr);
}

static bool _HighState__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  ros2_unitree_legged_msgs__msg__HighState * ros_message = static_cast<ros2_unitree_legged_msgs__msg__HighState *>(untyped_ros_message);
  (void)ros_message;
  return cdr_deserialize_ros2_unitree_legged_msgs__msg__HighState(cdr, ros_message);
}

static uint32_t _HighState__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_ros2_unitree_legged_msgs__msg__HighState(
      untyped_ros_message, 0));
}

static size_t _HighState__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_ros2_unitree_legged_msgs__msg__HighState(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_HighState = {
  "ros2_unitree_legged_msgs::msg",
  "HighState",
  _HighState__cdr_serialize,
  _HighState__cdr_deserialize,
  _HighState__get_serialized_size,
  _HighState__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _HighState__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_HighState,
  get_message_typesupport_handle_function,
  &ros2_unitree_legged_msgs__msg__HighState__get_type_hash,
  &ros2_unitree_legged_msgs__msg__HighState__get_type_description,
  &ros2_unitree_legged_msgs__msg__HighState__get_type_description_sources,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, ros2_unitree_legged_msgs, msg, HighState)() {
  return &_HighState__type_support;
}

#if defined(__cplusplus)
}
#endif

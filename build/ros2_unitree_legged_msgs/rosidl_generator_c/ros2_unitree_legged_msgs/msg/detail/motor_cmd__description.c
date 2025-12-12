// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/MotorCmd.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/motor_cmd__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__MotorCmd__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x94, 0xc8, 0xa4, 0xff, 0x8d, 0x5d, 0x43, 0xb4,
      0xf7, 0x36, 0x25, 0x71, 0x27, 0xc4, 0x46, 0xf6,
      0xad, 0xad, 0x87, 0x85, 0xfc, 0x91, 0xf9, 0xb5,
      0x5b, 0x95, 0xdc, 0x18, 0x8f, 0x5e, 0xd0, 0x6d,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char ros2_unitree_legged_msgs__msg__MotorCmd__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/MotorCmd";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__mode[] = "mode";
static char ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__q[] = "q";
static char ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__dq[] = "dq";
static char ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__tau[] = "tau";
static char ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__kp[] = "kp";
static char ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__kd[] = "kd";
static char ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__reserve[] = "reserve";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__MotorCmd__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__mode, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__q, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__dq, 2, 2},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__tau, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__kp, 2, 2},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__kd, 2, 2},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorCmd__FIELD_NAME__reserve, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32_ARRAY,
      3,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__MotorCmd__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__MotorCmd__TYPE_NAME, 37, 37},
      {ros2_unitree_legged_msgs__msg__MotorCmd__FIELDS, 7, 7},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "uint8 mode           # motor target mode\n"
  "float32 q            # motor target position\n"
  "float32 dq           # motor target velocity\n"
  "float32 tau          # motor target torque\n"
  "float32 kp           # motor spring stiffness coefficient\n"
  "float32 kd           # motor damper coefficient\n"
  "uint32[3] reserve    # motor target torque";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__MotorCmd__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__MotorCmd__TYPE_NAME, 37, 37},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 322, 322},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__MotorCmd__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__MotorCmd__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/MotorState.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/motor_state__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__MotorState__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x3f, 0x52, 0x4c, 0x9d, 0x84, 0xe0, 0x2c, 0xc7,
      0x05, 0x3e, 0x69, 0xda, 0x5a, 0x1a, 0xc4, 0xb2,
      0x0a, 0x99, 0xe2, 0xa7, 0x67, 0xcf, 0x95, 0x8b,
      0x5c, 0x4d, 0x30, 0x98, 0xdf, 0x07, 0xdf, 0xb8,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char ros2_unitree_legged_msgs__msg__MotorState__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/MotorState";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__mode[] = "mode";
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__q[] = "q";
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__dq[] = "dq";
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__ddq[] = "ddq";
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__tau_est[] = "tau_est";
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__q_raw[] = "q_raw";
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__dq_raw[] = "dq_raw";
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__ddq_raw[] = "ddq_raw";
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__temperature[] = "temperature";
static char ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__reserve[] = "reserve";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__MotorState__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__mode, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__q, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__dq, 2, 2},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__ddq, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__tau_est, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__q_raw, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__dq_raw, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__ddq_raw, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__temperature, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__FIELD_NAME__reserve, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__MotorState__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__MotorState__TYPE_NAME, 39, 39},
      {ros2_unitree_legged_msgs__msg__MotorState__FIELDS, 10, 10},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "uint8 mode           # motor current mode \n"
  "float32 q            # motor current position\\xef\\xbc\\x88rad\\xef\\xbc\\x89\n"
  "float32 dq           # motor current speed\\xef\\xbc\\x88rad/s\\xef\\xbc\\x89\n"
  "float32 ddq          # motor current speed\\xef\\xbc\\x88rad/s\\xef\\xbc\\x89\n"
  "float32 tau_est       # current estimated output torque\\xef\\xbc\\x88N*m\\xef\\xbc\\x89\n"
  "float32 q_raw        # motor current position\\xef\\xbc\\x88rad\\xef\\xbc\\x89\n"
  "float32 dq_raw       # motor current speed\\xef\\xbc\\x88rad/s\\xef\\xbc\\x89\n"
  "float32 ddq_raw      # motor current speed\\xef\\xbc\\x88rad/s\\xef\\xbc\\x89\n"
  "int8 temperature     # motor temperature\\xef\\xbc\\x88slow conduction of temperature leads to lag\\xef\\xbc\\x89\n"
  "uint32[2] reserve";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__MotorState__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__MotorState__TYPE_NAME, 39, 39},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 509, 509},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__MotorState__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__MotorState__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/IMU.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/imu__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__IMU__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x22, 0xfc, 0x7a, 0x0e, 0xa5, 0x64, 0x14, 0x4f,
      0x41, 0x57, 0x3e, 0x58, 0xf0, 0x99, 0xc1, 0x7c,
      0x3b, 0x8a, 0x11, 0xd8, 0x95, 0xc6, 0x22, 0xd0,
      0x6b, 0xdb, 0x6a, 0x14, 0xc4, 0x8e, 0xbf, 0x09,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char ros2_unitree_legged_msgs__msg__IMU__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/IMU";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__quaternion[] = "quaternion";
static char ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__gyroscope[] = "gyroscope";
static char ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__accelerometer[] = "accelerometer";
static char ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__rpy[] = "rpy";
static char ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__temperature[] = "temperature";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__IMU__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__quaternion, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      4,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__gyroscope, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      3,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__accelerometer, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      3,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__rpy, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      3,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__IMU__FIELD_NAME__temperature, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__IMU__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__IMU__TYPE_NAME, 32, 32},
      {ros2_unitree_legged_msgs__msg__IMU__FIELDS, 5, 5},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "float32[4] quaternion\n"
  "float32[3] gyroscope\n"
  "float32[3] accelerometer\n"
  "float32[3] rpy\n"
  "int8 temperature";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__IMU__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__IMU__TYPE_NAME, 32, 32},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 99, 99},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__IMU__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__IMU__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

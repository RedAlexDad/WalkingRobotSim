// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/Cartesian.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/cartesian__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__Cartesian__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x12, 0xf9, 0x58, 0xa9, 0x2c, 0xfa, 0x71, 0xf4,
      0x23, 0xe6, 0x83, 0xe2, 0x61, 0xff, 0xfc, 0x76,
      0x50, 0xb3, 0xcd, 0x7d, 0x33, 0xb5, 0x7f, 0x2b,
      0x16, 0x3b, 0x9d, 0x2d, 0xdb, 0x56, 0x38, 0xee,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char ros2_unitree_legged_msgs__msg__Cartesian__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/Cartesian";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__Cartesian__FIELD_NAME__x[] = "x";
static char ros2_unitree_legged_msgs__msg__Cartesian__FIELD_NAME__y[] = "y";
static char ros2_unitree_legged_msgs__msg__Cartesian__FIELD_NAME__z[] = "z";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__Cartesian__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__Cartesian__FIELD_NAME__x, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__Cartesian__FIELD_NAME__y, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__Cartesian__FIELD_NAME__z, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__Cartesian__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__Cartesian__TYPE_NAME, 38, 38},
      {ros2_unitree_legged_msgs__msg__Cartesian__FIELDS, 3, 3},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "float32 x\n"
  "float32 y\n"
  "float32 z";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__Cartesian__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__Cartesian__TYPE_NAME, 38, 38},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 29, 29},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__Cartesian__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__Cartesian__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

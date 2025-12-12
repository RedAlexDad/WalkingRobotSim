// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/LED.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/led__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__LED__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x69, 0xa4, 0x92, 0x1a, 0xf6, 0x83, 0x0a, 0xf7,
      0x77, 0x80, 0x69, 0x98, 0x5d, 0x47, 0x3d, 0xa9,
      0x6c, 0x31, 0x7b, 0xb7, 0x27, 0xbb, 0xcb, 0x56,
      0xae, 0xe8, 0xcd, 0xcc, 0x7d, 0xa6, 0x1b, 0xd6,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char ros2_unitree_legged_msgs__msg__LED__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/LED";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__LED__FIELD_NAME__r[] = "r";
static char ros2_unitree_legged_msgs__msg__LED__FIELD_NAME__g[] = "g";
static char ros2_unitree_legged_msgs__msg__LED__FIELD_NAME__b[] = "b";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__LED__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__LED__FIELD_NAME__r, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LED__FIELD_NAME__g, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LED__FIELD_NAME__b, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__LED__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__LED__TYPE_NAME, 32, 32},
      {ros2_unitree_legged_msgs__msg__LED__FIELDS, 3, 3},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "uint8 r\n"
  "uint8 g\n"
  "uint8 b";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__LED__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__LED__TYPE_NAME, 32, 32},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 23, 23},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__LED__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__LED__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

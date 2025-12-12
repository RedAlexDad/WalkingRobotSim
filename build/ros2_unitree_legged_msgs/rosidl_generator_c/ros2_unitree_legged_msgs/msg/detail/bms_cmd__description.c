// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/BmsCmd.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/bms_cmd__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__BmsCmd__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xb8, 0x80, 0x44, 0xbc, 0xa1, 0x6b, 0xc9, 0x1d,
      0x18, 0x5f, 0x81, 0xda, 0x1f, 0xdd, 0x81, 0x88,
      0x57, 0x5b, 0xd0, 0x0b, 0xaa, 0xc4, 0x3a, 0xdf,
      0x70, 0x63, 0x4a, 0xbc, 0x40, 0x18, 0x62, 0x79,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char ros2_unitree_legged_msgs__msg__BmsCmd__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/BmsCmd";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__BmsCmd__FIELD_NAME__off[] = "off";
static char ros2_unitree_legged_msgs__msg__BmsCmd__FIELD_NAME__reserve[] = "reserve";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__BmsCmd__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__BmsCmd__FIELD_NAME__off, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__BmsCmd__FIELD_NAME__reserve, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8_ARRAY,
      3,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__BmsCmd__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__BmsCmd__TYPE_NAME, 35, 35},
      {ros2_unitree_legged_msgs__msg__BmsCmd__FIELDS, 2, 2},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "uint8 off            # off 0xA5\n"
  "uint8[3] reserve";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__BmsCmd__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__BmsCmd__TYPE_NAME, 35, 35},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 48, 48},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__BmsCmd__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__BmsCmd__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/BmsState.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/bms_state__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__BmsState__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xb3, 0x2d, 0xc8, 0x0b, 0x26, 0x52, 0x84, 0x21,
      0x21, 0x3e, 0xc7, 0xf4, 0x5d, 0x6a, 0xcd, 0xa7,
      0x08, 0x28, 0x99, 0x83, 0xcf, 0x67, 0x39, 0x37,
      0xd0, 0x79, 0x63, 0x86, 0x06, 0x46, 0x9e, 0x92,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char ros2_unitree_legged_msgs__msg__BmsState__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/BmsState";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__version_h[] = "version_h";
static char ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__version_l[] = "version_l";
static char ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__bms_status[] = "bms_status";
static char ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__soc[] = "soc";
static char ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__current[] = "current";
static char ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__cycle[] = "cycle";
static char ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__bq_ntc[] = "bq_ntc";
static char ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__mcu_ntc[] = "mcu_ntc";
static char ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__cell_vol[] = "cell_vol";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__BmsState__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__version_h, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__version_l, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__bms_status, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__soc, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__current, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__cycle, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__bq_ntc, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT8_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__mcu_ntc, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT8_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__BmsState__FIELD_NAME__cell_vol, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16_ARRAY,
      10,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__BmsState__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__BmsState__TYPE_NAME, 37, 37},
      {ros2_unitree_legged_msgs__msg__BmsState__FIELDS, 9, 9},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "uint8 version_h\n"
  "uint8 version_l\n"
  "uint8 bms_status\n"
  "uint8 soc                  # SOC 0-100%\n"
  "int32 current              # mA\n"
  "uint16 cycle\n"
  "int8[2] bq_ntc             # x1 degrees centigrade\n"
  "int8[2] mcu_ntc            # x1 degrees centigrade\n"
  "uint16[10] cell_vol        # cell voltage mV";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__BmsState__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__BmsState__TYPE_NAME, 37, 37},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 280, 280},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__BmsState__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__BmsState__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

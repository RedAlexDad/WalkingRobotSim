// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/LowCmd.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/low_cmd__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__LowCmd__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x8e, 0x6b, 0xa9, 0xa2, 0x0e, 0x67, 0xb5, 0xd4,
      0xb5, 0x47, 0xf4, 0x2b, 0x8d, 0x71, 0x87, 0x0f,
      0xc5, 0xe9, 0x3e, 0x1d, 0x85, 0xf3, 0xa7, 0x82,
      0x60, 0x3e, 0x4a, 0x85, 0x40, 0x74, 0x25, 0x3e,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "ros2_unitree_legged_msgs/msg/detail/motor_cmd__functions.h"
#include "ros2_unitree_legged_msgs/msg/detail/bms_cmd__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t ros2_unitree_legged_msgs__msg__BmsCmd__EXPECTED_HASH = {1, {
    0xb8, 0x80, 0x44, 0xbc, 0xa1, 0x6b, 0xc9, 0x1d,
    0x18, 0x5f, 0x81, 0xda, 0x1f, 0xdd, 0x81, 0x88,
    0x57, 0x5b, 0xd0, 0x0b, 0xaa, 0xc4, 0x3a, 0xdf,
    0x70, 0x63, 0x4a, 0xbc, 0x40, 0x18, 0x62, 0x79,
  }};
static const rosidl_type_hash_t ros2_unitree_legged_msgs__msg__MotorCmd__EXPECTED_HASH = {1, {
    0x94, 0xc8, 0xa4, 0xff, 0x8d, 0x5d, 0x43, 0xb4,
    0xf7, 0x36, 0x25, 0x71, 0x27, 0xc4, 0x46, 0xf6,
    0xad, 0xad, 0x87, 0x85, 0xfc, 0x91, 0xf9, 0xb5,
    0x5b, 0x95, 0xdc, 0x18, 0x8f, 0x5e, 0xd0, 0x6d,
  }};
#endif

static char ros2_unitree_legged_msgs__msg__LowCmd__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/LowCmd";
static char ros2_unitree_legged_msgs__msg__BmsCmd__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/BmsCmd";
static char ros2_unitree_legged_msgs__msg__MotorCmd__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/MotorCmd";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__head[] = "head";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__level_flag[] = "level_flag";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__frame_reserve[] = "frame_reserve";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__sn[] = "sn";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__version[] = "version";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__band_width[] = "band_width";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__motor_cmd[] = "motor_cmd";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__bms[] = "bms";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__wireless_remote[] = "wireless_remote";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__reserve[] = "reserve";
static char ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__crc[] = "crc";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__LowCmd__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__head, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__level_flag, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__frame_reserve, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__sn, 2, 2},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__version, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__band_width, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__motor_cmd, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_ARRAY,
      20,
      0,
      {ros2_unitree_legged_msgs__msg__MotorCmd__TYPE_NAME, 37, 37},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__bms, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {ros2_unitree_legged_msgs__msg__BmsCmd__TYPE_NAME, 35, 35},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__wireless_remote, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8_ARRAY,
      40,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__reserve, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LowCmd__FIELD_NAME__crc, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription ros2_unitree_legged_msgs__msg__LowCmd__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {ros2_unitree_legged_msgs__msg__BmsCmd__TYPE_NAME, 35, 35},
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorCmd__TYPE_NAME, 37, 37},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__LowCmd__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__LowCmd__TYPE_NAME, 35, 35},
      {ros2_unitree_legged_msgs__msg__LowCmd__FIELDS, 11, 11},
    },
    {ros2_unitree_legged_msgs__msg__LowCmd__REFERENCED_TYPE_DESCRIPTIONS, 2, 2},
  };
  if (!constructed) {
    assert(0 == memcmp(&ros2_unitree_legged_msgs__msg__BmsCmd__EXPECTED_HASH, ros2_unitree_legged_msgs__msg__BmsCmd__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = ros2_unitree_legged_msgs__msg__BmsCmd__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&ros2_unitree_legged_msgs__msg__MotorCmd__EXPECTED_HASH, ros2_unitree_legged_msgs__msg__MotorCmd__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[1].fields = ros2_unitree_legged_msgs__msg__MotorCmd__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "\n"
  "uint8[2] head\n"
  "uint8 level_flag\n"
  "uint8 frame_reserve\n"
  "\n"
  "uint32[2] sn\n"
  "uint32[2] version\n"
  "uint16 band_width\n"
  "MotorCmd[20] motor_cmd\n"
  "BmsCmd bms\n"
  "uint8[40] wireless_remote\n"
  "uint32 reserve\n"
  "\n"
  "uint32 crc";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__LowCmd__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__LowCmd__TYPE_NAME, 35, 35},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 188, 188},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__LowCmd__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[3];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 3, 3};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__LowCmd__get_individual_type_description_source(NULL),
    sources[1] = *ros2_unitree_legged_msgs__msg__BmsCmd__get_individual_type_description_source(NULL);
    sources[2] = *ros2_unitree_legged_msgs__msg__MotorCmd__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}

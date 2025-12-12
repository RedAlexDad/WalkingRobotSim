// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/HighCmd.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/high_cmd__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__HighCmd__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xe0, 0xe3, 0x1b, 0x21, 0xff, 0x1d, 0xda, 0x9b,
      0x4e, 0x4c, 0x1b, 0xee, 0x09, 0x6a, 0xca, 0x24,
      0x7a, 0x73, 0x8f, 0x56, 0x2a, 0x27, 0x35, 0x38,
      0xc1, 0x7b, 0x1c, 0x1c, 0x89, 0x56, 0xcf, 0x70,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "ros2_unitree_legged_msgs/msg/detail/bms_cmd__functions.h"
#include "ros2_unitree_legged_msgs/msg/detail/led__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t ros2_unitree_legged_msgs__msg__BmsCmd__EXPECTED_HASH = {1, {
    0xb8, 0x80, 0x44, 0xbc, 0xa1, 0x6b, 0xc9, 0x1d,
    0x18, 0x5f, 0x81, 0xda, 0x1f, 0xdd, 0x81, 0x88,
    0x57, 0x5b, 0xd0, 0x0b, 0xaa, 0xc4, 0x3a, 0xdf,
    0x70, 0x63, 0x4a, 0xbc, 0x40, 0x18, 0x62, 0x79,
  }};
static const rosidl_type_hash_t ros2_unitree_legged_msgs__msg__LED__EXPECTED_HASH = {1, {
    0x69, 0xa4, 0x92, 0x1a, 0xf6, 0x83, 0x0a, 0xf7,
    0x77, 0x80, 0x69, 0x98, 0x5d, 0x47, 0x3d, 0xa9,
    0x6c, 0x31, 0x7b, 0xb7, 0x27, 0xbb, 0xcb, 0x56,
    0xae, 0xe8, 0xcd, 0xcc, 0x7d, 0xa6, 0x1b, 0xd6,
  }};
#endif

static char ros2_unitree_legged_msgs__msg__HighCmd__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/HighCmd";
static char ros2_unitree_legged_msgs__msg__BmsCmd__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/BmsCmd";
static char ros2_unitree_legged_msgs__msg__LED__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/LED";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__head[] = "head";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__level_flag[] = "level_flag";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__frame_reserve[] = "frame_reserve";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__sn[] = "sn";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__version[] = "version";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__band_width[] = "band_width";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__mode[] = "mode";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__gait_type[] = "gait_type";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__speed_level[] = "speed_level";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__foot_raise_height[] = "foot_raise_height";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__body_height[] = "body_height";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__position[] = "position";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__euler[] = "euler";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__velocity[] = "velocity";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__yaw_speed[] = "yaw_speed";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__bms[] = "bms";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__led[] = "led";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__wireless_remote[] = "wireless_remote";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__reserve[] = "reserve";
static char ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__crc[] = "crc";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__HighCmd__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__head, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__level_flag, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__frame_reserve, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__sn, 2, 2},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__version, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__band_width, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__mode, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__gait_type, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__speed_level, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__foot_raise_height, 17, 17},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__body_height, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__position, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__euler, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      3,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__velocity, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__yaw_speed, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__bms, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {ros2_unitree_legged_msgs__msg__BmsCmd__TYPE_NAME, 35, 35},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__led, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_ARRAY,
      4,
      0,
      {ros2_unitree_legged_msgs__msg__LED__TYPE_NAME, 32, 32},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__wireless_remote, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8_ARRAY,
      40,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__reserve, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighCmd__FIELD_NAME__crc, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription ros2_unitree_legged_msgs__msg__HighCmd__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {ros2_unitree_legged_msgs__msg__BmsCmd__TYPE_NAME, 35, 35},
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__LED__TYPE_NAME, 32, 32},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__HighCmd__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__HighCmd__TYPE_NAME, 36, 36},
      {ros2_unitree_legged_msgs__msg__HighCmd__FIELDS, 20, 20},
    },
    {ros2_unitree_legged_msgs__msg__HighCmd__REFERENCED_TYPE_DESCRIPTIONS, 2, 2},
  };
  if (!constructed) {
    assert(0 == memcmp(&ros2_unitree_legged_msgs__msg__BmsCmd__EXPECTED_HASH, ros2_unitree_legged_msgs__msg__BmsCmd__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = ros2_unitree_legged_msgs__msg__BmsCmd__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&ros2_unitree_legged_msgs__msg__LED__EXPECTED_HASH, ros2_unitree_legged_msgs__msg__LED__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[1].fields = ros2_unitree_legged_msgs__msg__LED__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "uint8[2] head\n"
  "uint8 level_flag\n"
  "uint8 frame_reserve\n"
  "\n"
  "uint32[2] sn\n"
  "uint32[2] version\n"
  "uint16 band_width\n"
  "uint8 mode \n"
  "\n"
  "uint8 gait_type\\t\\t   \n"
  "uint8 speed_level\\t\\t\\t   \n"
  "float32 foot_raise_height\\t\\t   \n"
  "float32 body_height\\t   \n"
  "float32[2] position \n"
  "float32[3] euler\\t   \n"
  "float32[2] velocity \n"
  "float32 yaw_speed\\t\\t\\t\\t   \n"
  "BmsCmd bms\n"
  "LED[4] led\n"
  "uint8[40] wireless_remote\n"
  "uint32 reserve\n"
  "\n"
  "uint32 crc";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__HighCmd__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__HighCmd__TYPE_NAME, 36, 36},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 376, 376},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__HighCmd__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[3];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 3, 3};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__HighCmd__get_individual_type_description_source(NULL),
    sources[1] = *ros2_unitree_legged_msgs__msg__BmsCmd__get_individual_type_description_source(NULL);
    sources[2] = *ros2_unitree_legged_msgs__msg__LED__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}

// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from ros2_unitree_legged_msgs:msg/HighState.idl
// generated code does not contain a copyright notice

#include "ros2_unitree_legged_msgs/msg/detail/high_state__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_ros2_unitree_legged_msgs
const rosidl_type_hash_t *
ros2_unitree_legged_msgs__msg__HighState__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xbd, 0xbb, 0x65, 0xc1, 0x8a, 0xb3, 0x21, 0x67,
      0xae, 0x6d, 0xb4, 0xb7, 0x4d, 0x64, 0x25, 0x0e,
      0xd1, 0x58, 0x73, 0x04, 0x4a, 0xd4, 0xcb, 0xfa,
      0x04, 0x97, 0x13, 0x14, 0xc7, 0x66, 0x27, 0x7f,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "ros2_unitree_legged_msgs/msg/detail/bms_state__functions.h"
#include "ros2_unitree_legged_msgs/msg/detail/motor_state__functions.h"
#include "ros2_unitree_legged_msgs/msg/detail/imu__functions.h"
#include "ros2_unitree_legged_msgs/msg/detail/cartesian__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t ros2_unitree_legged_msgs__msg__BmsState__EXPECTED_HASH = {1, {
    0xb3, 0x2d, 0xc8, 0x0b, 0x26, 0x52, 0x84, 0x21,
    0x21, 0x3e, 0xc7, 0xf4, 0x5d, 0x6a, 0xcd, 0xa7,
    0x08, 0x28, 0x99, 0x83, 0xcf, 0x67, 0x39, 0x37,
    0xd0, 0x79, 0x63, 0x86, 0x06, 0x46, 0x9e, 0x92,
  }};
static const rosidl_type_hash_t ros2_unitree_legged_msgs__msg__Cartesian__EXPECTED_HASH = {1, {
    0x12, 0xf9, 0x58, 0xa9, 0x2c, 0xfa, 0x71, 0xf4,
    0x23, 0xe6, 0x83, 0xe2, 0x61, 0xff, 0xfc, 0x76,
    0x50, 0xb3, 0xcd, 0x7d, 0x33, 0xb5, 0x7f, 0x2b,
    0x16, 0x3b, 0x9d, 0x2d, 0xdb, 0x56, 0x38, 0xee,
  }};
static const rosidl_type_hash_t ros2_unitree_legged_msgs__msg__IMU__EXPECTED_HASH = {1, {
    0x22, 0xfc, 0x7a, 0x0e, 0xa5, 0x64, 0x14, 0x4f,
    0x41, 0x57, 0x3e, 0x58, 0xf0, 0x99, 0xc1, 0x7c,
    0x3b, 0x8a, 0x11, 0xd8, 0x95, 0xc6, 0x22, 0xd0,
    0x6b, 0xdb, 0x6a, 0x14, 0xc4, 0x8e, 0xbf, 0x09,
  }};
static const rosidl_type_hash_t ros2_unitree_legged_msgs__msg__MotorState__EXPECTED_HASH = {1, {
    0x3f, 0x52, 0x4c, 0x9d, 0x84, 0xe0, 0x2c, 0xc7,
    0x05, 0x3e, 0x69, 0xda, 0x5a, 0x1a, 0xc4, 0xb2,
    0x0a, 0x99, 0xe2, 0xa7, 0x67, 0xcf, 0x95, 0x8b,
    0x5c, 0x4d, 0x30, 0x98, 0xdf, 0x07, 0xdf, 0xb8,
  }};
#endif

static char ros2_unitree_legged_msgs__msg__HighState__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/HighState";
static char ros2_unitree_legged_msgs__msg__BmsState__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/BmsState";
static char ros2_unitree_legged_msgs__msg__Cartesian__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/Cartesian";
static char ros2_unitree_legged_msgs__msg__IMU__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/IMU";
static char ros2_unitree_legged_msgs__msg__MotorState__TYPE_NAME[] = "ros2_unitree_legged_msgs/msg/MotorState";

// Define type names, field names, and default values
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__head[] = "head";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__level_flag[] = "level_flag";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__frame_reserve[] = "frame_reserve";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__sn[] = "sn";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__version[] = "version";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__band_width[] = "band_width";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__imu[] = "imu";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__motor_state[] = "motor_state";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__bms[] = "bms";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_force[] = "foot_force";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_force_est[] = "foot_force_est";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__mode[] = "mode";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__progress[] = "progress";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__gait_type[] = "gait_type";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_raise_height[] = "foot_raise_height";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__position[] = "position";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__body_height[] = "body_height";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__velocity[] = "velocity";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__yaw_speed[] = "yaw_speed";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__range_obstacle[] = "range_obstacle";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_position2body[] = "foot_position2body";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_speed2body[] = "foot_speed2body";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__wireless_remote[] = "wireless_remote";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__reserve[] = "reserve";
static char ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__crc[] = "crc";

static rosidl_runtime_c__type_description__Field ros2_unitree_legged_msgs__msg__HighState__FIELDS[] = {
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__head, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__level_flag, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__frame_reserve, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__sn, 2, 2},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__version, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32_ARRAY,
      2,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__band_width, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__imu, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {ros2_unitree_legged_msgs__msg__IMU__TYPE_NAME, 32, 32},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__motor_state, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_ARRAY,
      20,
      0,
      {ros2_unitree_legged_msgs__msg__MotorState__TYPE_NAME, 39, 39},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__bms, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {ros2_unitree_legged_msgs__msg__BmsState__TYPE_NAME, 37, 37},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_force, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT16_ARRAY,
      4,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_force_est, 14, 14},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT16_ARRAY,
      4,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__mode, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__progress, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__gait_type, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_raise_height, 17, 17},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__position, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      3,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__body_height, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__velocity, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      3,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__yaw_speed, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__range_obstacle, 14, 14},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_ARRAY,
      4,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_position2body, 18, 18},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_ARRAY,
      4,
      0,
      {ros2_unitree_legged_msgs__msg__Cartesian__TYPE_NAME, 38, 38},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__foot_speed2body, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_ARRAY,
      4,
      0,
      {ros2_unitree_legged_msgs__msg__Cartesian__TYPE_NAME, 38, 38},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__wireless_remote, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8_ARRAY,
      40,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__reserve, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__HighState__FIELD_NAME__crc, 3, 3},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription ros2_unitree_legged_msgs__msg__HighState__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {ros2_unitree_legged_msgs__msg__BmsState__TYPE_NAME, 37, 37},
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__Cartesian__TYPE_NAME, 38, 38},
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__IMU__TYPE_NAME, 32, 32},
    {NULL, 0, 0},
  },
  {
    {ros2_unitree_legged_msgs__msg__MotorState__TYPE_NAME, 39, 39},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
ros2_unitree_legged_msgs__msg__HighState__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {ros2_unitree_legged_msgs__msg__HighState__TYPE_NAME, 38, 38},
      {ros2_unitree_legged_msgs__msg__HighState__FIELDS, 25, 25},
    },
    {ros2_unitree_legged_msgs__msg__HighState__REFERENCED_TYPE_DESCRIPTIONS, 4, 4},
  };
  if (!constructed) {
    assert(0 == memcmp(&ros2_unitree_legged_msgs__msg__BmsState__EXPECTED_HASH, ros2_unitree_legged_msgs__msg__BmsState__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = ros2_unitree_legged_msgs__msg__BmsState__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&ros2_unitree_legged_msgs__msg__Cartesian__EXPECTED_HASH, ros2_unitree_legged_msgs__msg__Cartesian__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[1].fields = ros2_unitree_legged_msgs__msg__Cartesian__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&ros2_unitree_legged_msgs__msg__IMU__EXPECTED_HASH, ros2_unitree_legged_msgs__msg__IMU__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[2].fields = ros2_unitree_legged_msgs__msg__IMU__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&ros2_unitree_legged_msgs__msg__MotorState__EXPECTED_HASH, ros2_unitree_legged_msgs__msg__MotorState__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[3].fields = ros2_unitree_legged_msgs__msg__MotorState__get_type_description(NULL)->type_description.fields;
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
  "IMU imu\n"
  "MotorState[20] motor_state\n"
  "BmsState bms\n"
  "int16[4] foot_force\n"
  "int16[4] foot_force_est\n"
  "uint8 mode\n"
  "float32 progress\n"
  "uint8 gait_type\\t\\t   \n"
  "float32 foot_raise_height\\t\\t  \n"
  "float32[3] position \n"
  "float32 body_height\\t\\t\\t  \n"
  "float32[3] velocity \n"
  "float32 yaw_speed\\t\\t\\t\\t   \n"
  "float32[4] range_obstacle\n"
  "Cartesian[4] foot_position2body \n"
  "Cartesian[4] foot_speed2body\\t\n"
  "uint8[40] wireless_remote\n"
  "uint32 reserve\n"
  "\n"
  "uint32 crc";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
ros2_unitree_legged_msgs__msg__HighState__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {ros2_unitree_legged_msgs__msg__HighState__TYPE_NAME, 38, 38},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 506, 506},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
ros2_unitree_legged_msgs__msg__HighState__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[5];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 5, 5};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *ros2_unitree_legged_msgs__msg__HighState__get_individual_type_description_source(NULL),
    sources[1] = *ros2_unitree_legged_msgs__msg__BmsState__get_individual_type_description_source(NULL);
    sources[2] = *ros2_unitree_legged_msgs__msg__Cartesian__get_individual_type_description_source(NULL);
    sources[3] = *ros2_unitree_legged_msgs__msg__IMU__get_individual_type_description_source(NULL);
    sources[4] = *ros2_unitree_legged_msgs__msg__MotorState__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}

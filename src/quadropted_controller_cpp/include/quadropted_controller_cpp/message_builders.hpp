#pragma once
#include "quadropted_controller_cpp/message_builders.hpp"

// Структуры данных для message_builders
namespace quadropted {

struct OdometryData {
    std::string header_frame_id, header_stamp, child_frame_id;
    Position pose_position;
    Quaternion pose_orientation;
    TwistLin twist_linear;
    TwistAng twist_angular;
};

struct TFData {
    std::string header_frame_id, child_frame_id, stamp;
    Position translation;
    Quaternion rotation;
};

struct MarkerData {
    std::string frame_id, stamp;
    int id;
    double position_x, position_y, position_z;
    double scale;
    double color_r, color_g, color_b;
};

}

#pragma once
#include <cmath>
#include <string>
#include <vector>
#include <array>

namespace quadropted {

struct Quaternion { double x, y, z, w; };
struct Position  { double x, y, z; };
struct TwistLin  { double x, y, z; };
struct TwistAng  { double x, y, z; };

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

inline Quaternion build_quaternion_from_yaw(double theta) {
    return {0.0, 0.0, std::sin(theta / 2.0), std::cos(theta / 2.0)};
}

inline OdometryData build_odometry_data(double x, double y, double theta,
                                         double linear_vx, double linear_vy, double angular_vz,
                                         const std::string& frame_id, const std::string& child_frame_id,
                                         const std::string& stamp) {
    return {frame_id, stamp, child_frame_id,
            {x, y, 0.0}, build_quaternion_from_yaw(theta),
            {linear_vx, linear_vy, 0.0}, {0.0, 0.0, angular_vz}};
}

inline TFData build_tf_data(double x, double y, double theta,
                             const std::string& frame_id, const std::string& child_frame_id,
                             const std::string& stamp) {
    return {frame_id, child_frame_id, stamp,
            {x, y, 0.0}, build_quaternion_from_yaw(theta)};
}

inline std::vector<MarkerData> build_marker_data(
    const std::vector<std::array<double, 3>>& foot_positions,
    const std::string& frame_id, const std::string& stamp,
    double marker_scale = 0.05)
{
    std::vector<MarkerData> markers;
    markers.reserve(foot_positions.size());
    for (size_t i = 0; i < foot_positions.size(); ++i) {
        markers.push_back({frame_id, stamp, static_cast<int>(i),
                          foot_positions[i][0], foot_positions[i][1], foot_positions[i][2],
                          marker_scale, 1.0, 0.0, 0.0});
    }
    return markers;
}

} // namespace quadropted

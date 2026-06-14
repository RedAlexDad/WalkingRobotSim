/// @file message_builders.hpp
/// @brief Построители ROS-сообщений для одометрии, TF и маркеров.
///
/// Формирует поля сообщений в C++-структурах (OdometryData, TFData, MarkerData)
/// для последующей публикации в ROS-топики. Отделяет логику построения данных
/// от ROS-инфраструктуры.
///
/// ## Структуры
/// - OdometryData: поза (position + quaternion) + twist (linear + angular)
/// - TFData: frame_id, child_frame_id, translation, rotation
/// - MarkerData: position, scale, color (RGBA) для визуализатора RViz
///
/// @warning build_marker_data() принимает положения лап как vector<array<double,3>>,
///   а LegsMatrix — это Eigen::Matrix3Xd. Вызывающий должен конвертировать явно.
///
/// @see DogOdometryNode, OdometryState

#pragma once
#include <array>
#include <string>
#include <vector>

namespace quadropted {

/// Кватернион для ROS-сообщений.
struct Quaternion { double x, y, z, w; };

/// Позиция для ROS-сообщений.
struct Position { double x, y, z; };

/// Линейная скорость (twist).
struct TwistLin { double x, y, z; };

/// Угловая скорость (twist).
struct TwistAng { double x, y, z; };

/// Предварительно сформированные поля сообщения nav_msgs/Odometry.
struct OdometryData {
    std::string header_frame_id, header_stamp, child_frame_id;
    Position pose_position;
    Quaternion pose_orientation;
    TwistLin twist_linear;
    TwistAng twist_angular;
};

/// Предварительно сформированные поля TF-сообщения.
struct TFData {
    std::string header_frame_id, child_frame_id, stamp;
    Position translation;
    Quaternion rotation;
};

/// Предварительно сформированные поля маркера для RViz.
struct MarkerData {
    std::string frame_id, stamp;
    int id;
    double position_x, position_y, position_z, scale;
    double color_r, color_g, color_b;
};

/// Построить кватернион из угла рыскания (yaw).
///
/// @param theta  Угол рыскания [рад].
///
/// @return Кватернион: w = cos(θ/2), z = sin(θ/2).
///
/// @note Для roll = pitch = 0 (движение по плоскости).
Quaternion build_quaternion_from_yaw(double theta);

/// Построить данные одометрии.
///
/// @param x,y,theta       Положение [м, м, рад]
/// @param linear_vx       Линейная скорость X [м/с]
/// @param linear_vy       Линейная скорость Y [м/с]
/// @param angular_vz      Угловая скорость Z [рад/с]
/// @param frame_id        Фрейм заголовка (обычно "odom")
/// @param child_frame_id  Дочерний фрейм (обычно "base")
/// @param stamp           Временная метка (строка)
///
/// @return Структура OdometryData с заполненными полями.
OdometryData build_odometry_data(double x, double y, double theta, double linear_vx, double linear_vy,
                                 double angular_vz, const std::string& frame_id, const std::string& child_frame_id,
                                 const std::string& stamp);

/// Построить TF-данные (трансформация odom → base).
///
/// @param x,y,theta       Положение [м, м, рад]
/// @param frame_id        Родительский фрейм ("odom")
/// @param child_frame_id  Дочерний фрейм ("base")
/// @param stamp           Временная метка
///
/// @return Структура TFData.
TFData build_tf_data(double x, double y, double theta, const std::string& frame_id, const std::string& child_frame_id,
                     const std::string& stamp);

/// Построить массив маркеров для отображения лап в RViz.
///
/// @param foot_positions  Положения лап [x,y,z]×4
/// @param frame_id        Фрейм ("odom" или "base")
/// @param stamp           Временная метка
/// @param marker_scale    Размер сферы маркера [м] (0.05 по умолчанию)
///
/// @return Вектор MarkerData (4 сферы, каждая своего цвета).
///
/// @note Цвета: FR=красный, FL=зелёный, RR=синий, RL=жёлтый.
std::vector<MarkerData> build_marker_data(const std::vector<std::array<double, 3>>& foot_positions,
                                          const std::string& frame_id, const std::string& stamp,
                                          double marker_scale = 0.05);

}  // namespace quadropted

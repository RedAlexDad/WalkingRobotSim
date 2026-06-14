/// @file dog_odometry_node.hpp
/// @brief Узел одометрии — слияние контактов лап + IMU + FK.
///
/// DogOdometryNode оценивает положение робота в плоскости (x, y, θ)
/// на основе данных:
/// - Положения лап (через ForwardKinematics)
/// - Контакты лап (RobotFootContact)
/// - IMU (sensor_msgs/Imu)
///
/// ## Алгоритм
/// ```
/// 1. imu_callback() — сохраняет угловую скорость и ускорения
/// 2. joint_states_callback() — вычисляет FK → foot_positions
/// 3. timer_callback (50 Гц) ← цикл управления:
///    a. foot_contacts → prev/current foot deltas
///    b. update_odometry_step() → скользящее среднее дельт
///    c. publish_odometry() → nav_msgs/Odometry
///    d. publish_markers() → RViz маркеры
///    e. publish_stall_status() → bool (пробуксовка)
/// ```
///
/// ## Топики
/// | Направление | Топик | Тип |
/// |------------|-------|-----|
/// | Input  | /imu | sensor_msgs/Imu |
/// | Input  | /joint_states | std_msgs/Float64MultiArray |
/// | Input  | /foot_contacts | RobotFootContact |
/// | Output | /odom | nav_msgs/Odometry |
/// | Output | /stall_status | std_msgs/Bool |
/// | Output | /foot_markers | MarkerArray |
/// | Output | /tf | TF |
///
/// @warning Одометрия дрейфует на скользких поверхностях (пробуксовка).
///   Используйте stall_pub_ для внешней коррекции.
///
/// @see OdometryState, ForwardKinematics, OdometryData

#pragma once

#include <tf2_ros/transform_broadcaster.h>

#include <memory>
#include <nav_msgs/msg/odometry.hpp>
#include <quadropted_msgs/msg/robot_foot_contact.hpp>
#include <quadropted_msgs/msg/robot_velocity.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <std_msgs/msg/bool.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <string>
#include <visualization_msgs/msg/marker_array.hpp>

#include "quadropted_controller_cpp/kinematics/forward_kinematics.hpp"
#include "quadropted_controller_cpp/odometry/odometry.hpp"

/// Узел одометрии: контакты лап + IMU → положение (x, y, θ).
///
/// Публикует nav_msgs/Odometry, TF (odom→base) и маркеры лап в RViz.
/// Работает на частоте 50 Гц (timer_callback).
class DogOdometryNode : public rclcpp::Node {
  public:
    /// Конструктор: инициализирует подписчики, издатели, FK и OdometryState.
    ///
    /// Параметры читаются из YAML-конфига (robot_controller.yaml):
    ///   - body_length, body_width, l1–l4: геометрия
    ///   - filter_window_size: окно скользящего среднего
    ///   - stall_window, stall_ang_vel_threshold: детекция пробуксовки
    ///   - publish_rate: частота публикации
    ///   - enable_odom_tf: публиковать ли TF
    DogOdometryNode();

  private:
    void imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg);
    void joint_states_callback(const std_msgs::msg::Float64MultiArray::SharedPtr msg);
    void foot_contacts_callback(const quadropted_msgs::msg::RobotFootContact::SharedPtr msg);
    void calculate_foot_positions();
    void update_odometry_step();
    void publish_odometry();
    void publish_markers();
    void publish_stall_status();
    void timer_callback();

    std::unique_ptr<quadropted::ForwardKinematics> fk_;
    std::unique_ptr<quadropted::OdometryState> odom_state_;
    rclcpp::Time last_position_time_;

    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr stall_pub_;
    rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr marker_pub_;
    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;

    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
    rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr joint_states_sub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotFootContact>::SharedPtr foot_contacts_sub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotVelocity>::SharedPtr velocity_sub_;

    rclcpp::TimerBase::SharedPtr timer_;

    bool verbose_ = false;
    int publish_rate_ = 50;
    bool has_imu_heading_ = true;
    bool enable_odom_tf_ = false;
    std::string base_frame_id_ = "base";
    std::string odom_frame_id_ = "odom";
};

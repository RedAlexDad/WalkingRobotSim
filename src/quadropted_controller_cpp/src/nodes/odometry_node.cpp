#include "quadropted_controller_cpp/nodes/dog_odometry_node.hpp"

DogOdometryNode::DogOdometryNode() : Node("dog_odometry") {
    declare_parameter("verbose", false);
    declare_parameter("publish_rate", 50);
    declare_parameter("has_imu_heading", true);
    declare_parameter("enable_odom_tf", false);
    declare_parameter("base_frame_id", "base");
    declare_parameter("odom_frame_id", "odom");
    declare_parameter("filter_window_size", 14);
    declare_parameter("imu_topic", "imu_plugin/out");
    declare_parameter("stall_window", 20);
    declare_parameter("stall_ang_vel_threshold", 0.05);
    declare_parameter("stall_exit_ang_vel_threshold", 0.1);

    verbose_ = get_parameter("verbose").as_bool();
    publish_rate_ = get_parameter("publish_rate").as_int();
    has_imu_heading_ = get_parameter("has_imu_heading").as_bool();
    enable_odom_tf_ = get_parameter("enable_odom_tf").as_bool();
    base_frame_id_ = get_parameter("base_frame_id").as_string();
    odom_frame_id_ = get_parameter("odom_frame_id").as_string();
    int filter_window = static_cast<int>(get_parameter("filter_window_size").as_int());
    std::string imu_topic = get_parameter("imu_topic").as_string();

    double body_length = 0.3762, body_width = 0.0935;
    double l1 = 0.0, l2 = 0.0955, l3 = 0.213, l4 = 0.213;
    fk_ = std::make_unique<quadropted::ForwardKinematics>(body_length, body_width, l1, l2, l3, l4);

    odom_state_ = std::make_unique<quadropted::OdometryState>(filter_window);
    last_position_time_ = now();

    odom_state_->stall_window = get_parameter("stall_window").as_int();
    odom_state_->stall_ang_vel_threshold = get_parameter("stall_ang_vel_threshold").as_double();
    odom_state_->stall_exit_ang_vel_threshold = get_parameter("stall_exit_ang_vel_threshold").as_double();

    odom_pub_ = create_publisher<nav_msgs::msg::Odometry>("odom", 10);
    stall_pub_ = create_publisher<std_msgs::msg::Bool>("stall_status", 10);
    marker_pub_ = create_publisher<visualization_msgs::msg::MarkerArray>("foot_markers", 10);

    if (enable_odom_tf_) {
        tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);
    }

    if (has_imu_heading_) {
        imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
            imu_topic, 10, [this](const sensor_msgs::msg::Imu::SharedPtr msg) { imu_callback(msg); });
    }

    joint_states_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
        "joint_group_controller/commands", 10,
        [this](const std_msgs::msg::Float64MultiArray::SharedPtr msg) { joint_states_callback(msg); });

    foot_contacts_sub_ = create_subscription<quadropted_msgs::msg::RobotFootContact>(
        "foot_contact", rclcpp::SensorDataQoS(),
        [this](const quadropted_msgs::msg::RobotFootContact::SharedPtr msg) { foot_contacts_callback(msg); });

    velocity_sub_ = create_subscription<quadropted_msgs::msg::RobotVelocity>(
        "robot_velocity", 10, [this](const quadropted_msgs::msg::RobotVelocity::SharedPtr msg) {
            if (msg->robot_id == 1) {
                odom_state_->linear_velocity_x = msg->cmd_vel.linear.x;
                odom_state_->linear_velocity_y = msg->cmd_vel.linear.y;
            }
        });

    double timer_period = 1.0 / static_cast<double>(publish_rate_);
    timer_ = create_wall_timer(std::chrono::duration<double>(timer_period), [this]() { timer_callback(); });

    RCLCPP_INFO(get_logger(), "Dog Odometry Node (C++) has been started.");
}

void DogOdometryNode::timer_callback() {
    calculate_foot_positions();
    update_odometry_step();
    publish_odometry();
    publish_stall_status();
    publish_markers();
}

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<DogOdometryNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}

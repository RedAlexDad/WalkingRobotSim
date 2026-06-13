#include <geometry_msgs/msg/transform_stamped.hpp>
#include <visualization_msgs/msg/marker.hpp>

#include "quadropted_controller_cpp/nodes/dog_odometry_node.hpp"

void DogOdometryNode::publish_odometry() {
    nav_msgs::msg::Odometry odom_msg;
    odom_msg.header.stamp = now();
    odom_msg.header.frame_id = odom_frame_id_;
    odom_msg.child_frame_id = base_frame_id_;

    odom_msg.pose.pose.position.x = odom_state_->x;
    odom_msg.pose.pose.position.y = odom_state_->y;
    odom_msg.pose.pose.position.z = 0.0;

    double half_theta = odom_state_->theta / 2.0;
    odom_msg.pose.pose.orientation.x = 0.0;
    odom_msg.pose.pose.orientation.y = 0.0;
    odom_msg.pose.pose.orientation.z = std::sin(half_theta);
    odom_msg.pose.pose.orientation.w = std::cos(half_theta);

    odom_msg.twist.twist.linear.x = odom_state_->linear_velocity_x;
    odom_msg.twist.twist.linear.y = odom_state_->linear_velocity_y;
    odom_msg.twist.twist.angular.z = odom_state_->imu_angular_velocity;

    odom_pub_->publish(odom_msg);

    if (enable_odom_tf_) {
        geometry_msgs::msg::TransformStamped tf_msg;
        tf_msg.header.stamp = odom_msg.header.stamp;
        tf_msg.header.frame_id = odom_frame_id_;
        tf_msg.child_frame_id = base_frame_id_;
        tf_msg.transform.translation.x = odom_state_->x;
        tf_msg.transform.translation.y = odom_state_->y;
        tf_msg.transform.translation.z = 0.0;
        tf_msg.transform.rotation = odom_msg.pose.pose.orientation;
        tf_broadcaster_->sendTransform(tf_msg);
    }
}

void DogOdometryNode::publish_markers() {
    visualization_msgs::msg::MarkerArray marker_array;
    auto now_stamp = now();

    const double colors[4][3] = {{1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, 0.0, 1.0}, {1.0, 1.0, 0.0}};

    for (int i = 0; i < 4; ++i) {
        visualization_msgs::msg::Marker marker;
        marker.header.stamp = now_stamp;
        marker.header.frame_id = base_frame_id_;
        marker.ns = "foot_markers";
        marker.id = i;
        marker.type = visualization_msgs::msg::Marker::SPHERE;
        marker.action = visualization_msgs::msg::Marker::ADD;
        marker.pose.position.x = odom_state_->foot_positions[i].x();
        marker.pose.position.y = odom_state_->foot_positions[i].y();
        marker.pose.position.z = odom_state_->foot_positions[i].z();
        marker.pose.orientation.w = 1.0;
        marker.scale.x = 0.05;
        marker.scale.y = 0.05;
        marker.scale.z = 0.05;
        marker.color.a = 1.0;
        marker.color.r = colors[i][0];
        marker.color.g = colors[i][1];
        marker.color.b = colors[i][2];
        marker_array.markers.push_back(marker);
    }

    marker_pub_->publish(marker_array);
}

void DogOdometryNode::publish_stall_status() {
    std_msgs::msg::Bool msg;
    msg.data = odom_state_->is_stalled;
    stall_pub_->publish(msg);
}

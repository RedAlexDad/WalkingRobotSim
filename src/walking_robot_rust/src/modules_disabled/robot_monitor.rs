//! Robot monitoring module

use r2r::*;
use anyhow::Result;
use crate::robot_state::{JointStates, RobotPose, RobotVelocity, RobotState};
use std::sync::Arc;
use tokio::sync::Mutex;

/// Robot monitor for tracking sensor data and state
pub struct RobotMonitor {
    joint_subscriber: r2r::Subscriber<r2r::sensor_msgs::msg::JointState>,
    odom_subscriber: r2r::Subscriber<r2r::nav_msgs::msg::Odometry>,
    imu_subscriber: r2r::Subscriber<r2r::sensor_msgs::msg::Imu>,
    latest_state: Arc<Mutex<RobotState>>,
}

impl RobotMonitor {
    /// Create a new robot monitor
    pub fn new(ctx: &r2r::Context) -> Result<Self> {
        let joint_subscriber = ctx.create_subscription::<r2r::sensor_msgs::msg::JointState>(
            "/joint_states",
            r2r::QosProfile::default(),
        )?;
        
        let odom_subscriber = ctx.create_subscription::<r2r::nav_msgs::msg::Odometry>(
            "/odom",
            r2r::QosProfile::default(),
        )?;
        
        let imu_subscriber = ctx.create_subscription::<r2r::sensor_msgs::msg::Imu>(
            "/imu",
            r2r::QosProfile::default(),
        )?;
        
        let latest_state = Arc::new(Mutex::new(RobotState::new()));
        
        Ok(Self {
            joint_subscriber,
            odom_subscriber,
            imu_subscriber,
            latest_state,
        })
    }
    
    /// Start monitoring sensor data
    pub async fn start_monitoring(&mut self) -> Result<()> {
        let state_clone = self.latest_state.clone();
        
        // Start joint state monitoring
        let mut joint_subscriber = self.joint_subscriber.clone();
        let joint_state_clone = state_clone.clone();
        tokio::spawn(async move {
            while let Ok(msg) = joint_subscriber.next().await {
                if let Err(e) = Self::process_joint_state(msg, &joint_state_clone).await {
                    eprintln!("Error processing joint state: {}", e);
                }
            }
        });
        
        // Start odometry monitoring
        let mut odom_subscriber = self.odom_subscriber.clone();
        let odom_state_clone = state_clone.clone();
        tokio::spawn(async move {
            while let Ok(msg) = odom_subscriber.next().await {
                if let Err(e) = Self::process_odometry(msg, &odom_state_clone).await {
                    eprintln!("Error processing odometry: {}", e);
                }
            }
        });
        
        // Start IMU monitoring
        let mut imu_subscriber = self.imu_subscriber.clone();
        let imu_state_clone = state_clone.clone();
        tokio::spawn(async move {
            while let Ok(msg) = imu_subscriber.next().await {
                if let Err(e) = Self::process_imu(msg, &imu_state_clone).await {
                    eprintln!("Error processing IMU: {}", e);
                }
            }
        });
        
        Ok(())
    }
    
    /// Get the latest robot state
    pub async fn get_latest_state(&self) -> Result<RobotState> {
        let state = self.latest_state.lock().await;
        Ok(state.clone())
    }
    
    /// Process joint state message
    async fn process_joint_state(
        msg: r2r::sensor_msgs::msg::JointState,
        state: &Arc<Mutex<RobotState>>,
    ) -> Result<()> {
        let mut robot_state = state.lock().await;
        
        // Map joint positions to our joint structure
        if msg.name.len() >= 12 && msg.position.len() >= 12 {
            robot_state.joints = JointStates {
                front_left_hip: msg.position[0],
                front_left_knee: msg.position[1],
                front_left_ankle: msg.position[2],
                front_right_hip: msg.position[3],
                front_right_knee: msg.position[4],
                front_right_ankle: msg.position[5],
                rear_left_hip: msg.position[6],
                rear_left_knee: msg.position[7],
                rear_left_ankle: msg.position[8],
                rear_right_hip: msg.position[9],
                rear_right_knee: msg.position[10],
                rear_right_ankle: msg.position[11],
            };
        }
        
        robot_state.check_stability();
        Ok(())
    }
    
    /// Process odometry message
    async fn process_odometry(
        msg: r2r::nav_msgs::msg::Odometry,
        state: &Arc<Mutex<RobotState>>,
    ) -> Result<()> {
        let mut robot_state = state.lock().await;
        
        // Update pose
        robot_state.pose.x = msg.pose.pose.position.x;
        robot_state.pose.y = msg.pose.pose.position.y;
        robot_state.pose.z = msg.pose.pose.position.z;
        
        // Extract orientation from quaternion
        let q = &msg.pose.pose.orientation;
        let (roll, pitch, yaw) = Self::quaternion_to_euler(q.x, q.y, q.z, q.w);
        
        robot_state.pose.roll = roll;
        robot_state.pose.pitch = pitch;
        robot_state.pose.yaw = yaw;
        
        // Update velocity
        robot_state.velocity.linear_x = msg.twist.twist.linear.x;
        robot_state.velocity.linear_y = msg.twist.twist.linear.y;
        robot_state.velocity.linear_z = msg.twist.twist.linear.z;
        robot_state.velocity.angular_x = msg.twist.twist.angular.x;
        robot_state.velocity.angular_y = msg.twist.twist.angular.y;
        robot_state.velocity.angular_z = msg.twist.twist.angular.z;
        
        Ok(())
    }
    
    /// Process IMU message
    async fn process_imu(
        msg: r2r::sensor_msgs::msg::Imu,
        state: &Arc<Mutex<RobotState>>,
    ) -> Result<()> {
        let mut robot_state = state.lock().await;
        
        // Extract orientation from quaternion
        let q = &msg.orientation;
        let (roll, pitch, yaw) = Self::quaternion_to_euler(q.x, q.y, q.z, q.w);
        
        // Update pose with IMU orientation (more accurate than odometry for orientation)
        robot_state.pose.roll = roll;
        robot_state.pose.pitch = pitch;
        robot_state.pose.yaw = yaw;
        
        robot_state.check_stability();
        Ok(())
    }
    
    /// Convert quaternion to Euler angles
    fn quaternion_to_euler(x: f64, y: f64, z: f64, w: f64) -> (f64, f64, f64) {
        // Roll (x-axis rotation)
        let sinr_cosp = 2.0 * (w * x + y * z);
        let cosr_cosp = 1.0 - 2.0 * (x * x + y * y);
        let roll = sinr_cosp.atan2(cosr_cosp);
        
        // Pitch (y-axis rotation)
        let sinp = 2.0 * (w * y - z * x);
        let pitch = if sinp.abs() >= 1.0 {
            sinp.signum() * std::f64::consts::PI / 2.0
        } else {
            sinp.asin()
        };
        
        // Yaw (z-axis rotation)
        let siny_cosp = 2.0 * (w * z + x * y);
        let cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
        let yaw = siny_cosp.atan2(cosy_cosp);
        
        (roll, pitch, yaw)
    }
    
    /// Get robot stability metrics
    pub async fn get_stability_metrics(&self) -> Result<StabilityMetrics> {
        let state = self.latest_state.lock().await;
        
        Ok(StabilityMetrics {
            is_stable: state.is_stable,
            center_of_mass_height: state.pose.z,
            pitch_angle: state.pose.pitch,
            roll_angle: state.pose.roll,
            support_polygon_area: self.calculate_support_polygon_area(&state.joints),
            stability_margin: self.calculate_stability_margin(&state),
        })
    }
    
    /// Calculate support polygon area
    fn calculate_support_polygon_area(&self, joints: &JointStates) -> f64 {
        // Simplified calculation based on foot positions
        // In a real implementation, this would use forward kinematics
        let foot_separation = 0.3; // meters
        let foot_length = 0.2; // meters
        
        foot_separation * foot_length
    }
    
    /// Calculate stability margin
    fn calculate_stability_margin(&self, state: &RobotState) -> f64 {
        // Simplified stability margin calculation
        let max_angle = std::f64::consts::PI / 6.0; // 30 degrees
        let current_angle = state.pose.pitch.abs().max(state.pose.roll.abs());
        
        max_angle - current_angle
    }
}

/// Stability metrics for monitoring
#[derive(Debug, Clone)]
pub struct StabilityMetrics {
    pub is_stable: bool,
    pub center_of_mass_height: f64,
    pub pitch_angle: f64,
    pub roll_angle: f64,
    pub support_polygon_area: f64,
    pub stability_margin: f64,
}

//! Robot controller module

use r2r::*;
use anyhow::Result;
use crate::robot_state::{JointStates, RobotState};
use std::f64::consts::PI;

/// Motion command for the robot
#[derive(Debug, Clone)]
pub struct MotionCommand {
    pub joint_positions: JointStates,
    pub duration: std::time::Duration,
    pub max_velocity: f64,
}

/// Robot controller for executing motions
pub struct RobotController {
    joint_publisher: r2r::Publisher<r2r::sensor_msgs::msg::JointState>,
    cmd_vel_publisher: r2r::Publisher<r2r::geometry_msgs::msg::Twist>,
    joint_limits: JointStates,
}

impl RobotController {
    /// Create a new robot controller
    pub fn new(ctx: &r2r::Context) -> Result<Self> {
        let joint_publisher = ctx.create_publisher::<r2r::sensor_msgs::msg::JointState>(
            "/joint_states",
            r2r::QosProfile::default(),
        )?;
        
        let cmd_vel_publisher = ctx.create_publisher::<r2r::geometry_msgs::msg::Twist>(
            "/cmd_vel",
            r2r::QosProfile::default(),
        )?;
        
        Ok(Self {
            joint_publisher,
            cmd_vel_publisher,
            joint_limits: RobotState::get_joint_limits(),
        })
    }
    
    /// Initialize the controller
    pub async fn initialize(&mut self) -> Result<()> {
        // Send initial joint positions
        let initial_joints = JointStates::default();
        self.send_joint_positions(initial_joints).await?;
        Ok(())
    }
    
    /// Send joint positions to the robot
    pub async fn send_joint_positions(&mut self, joints: JointStates) -> Result<()> {
        // Validate joint limits
        self.validate_joint_positions(&joints)?;
        
        let mut joint_state = r2r::sensor_msgs::msg::JointState::default();
        joint_state.header.stamp = r2r::Clock::now().into();
        
        joint_state.name = vec![
            "front_left_hip_joint".to_string(),
            "front_left_knee_joint".to_string(),
            "front_left_ankle_joint".to_string(),
            "front_right_hip_joint".to_string(),
            "front_right_knee_joint".to_string(),
            "front_right_ankle_joint".to_string(),
            "rear_left_hip_joint".to_string(),
            "rear_left_knee_joint".to_string(),
            "rear_left_ankle_joint".to_string(),
            "rear_right_hip_joint".to_string(),
            "rear_right_knee_joint".to_string(),
            "rear_right_ankle_joint".to_string(),
        ];
        
        joint_state.position = vec![
            joints.front_left_hip,
            joints.front_left_knee,
            joints.front_left_ankle,
            joints.front_right_hip,
            joints.front_right_knee,
            joints.front_right_ankle,
            joints.rear_left_hip,
            joints.rear_left_knee,
            joints.rear_left_ankle,
            joints.rear_right_hip,
            joints.rear_right_knee,
            joints.rear_right_ankle,
        ];
        
        joint_state.velocity = vec![0.0; 12];
        joint_state.effort = vec![0.0; 12];
        
        self.joint_publisher.publish(&joint_state)?;
        Ok(())
    }
    
    /// Send velocity command
    pub async fn send_velocity_command(&mut self, linear_x: f64, linear_y: f64, angular_z: f64) -> Result<()> {
        let mut twist = r2r::geometry_msgs::msg::Twist::default();
        
        twist.linear.x = linear_x;
        twist.linear.y = linear_y;
        twist.linear.z = 0.0;
        
        twist.angular.x = 0.0;
        twist.angular.y = 0.0;
        twist.angular.z = angular_z;
        
        self.cmd_vel_publisher.publish(&twist)?;
        Ok(())
    }
    
    /// Execute a motion command
    pub async fn execute_motion(&mut self, command: MotionCommand) -> Result<()> {
        let start_time = std::time::Instant::now();
        let target_joints = command.joint_positions;
        
        // Get current joint positions (would normally get from state)
        let current_joints = JointStates::default();
        
        while start_time.elapsed() < command.duration {
            let progress = start_time.elapsed().as_secs_f64() / command.duration.as_secs_f64();
            
            // Interpolate joint positions
            let interpolated_joints = JointStates {
                front_left_hip: self.interpolate(current_joints.front_left_hip, target_joints.front_left_hip, progress),
                front_left_knee: self.interpolate(current_joints.front_left_knee, target_joints.front_left_knee, progress),
                front_left_ankle: self.interpolate(current_joints.front_left_ankle, target_joints.front_left_ankle, progress),
                front_right_hip: self.interpolate(current_joints.front_right_hip, target_joints.front_right_hip, progress),
                front_right_knee: self.interpolate(current_joints.front_right_knee, target_joints.front_right_knee, progress),
                front_right_ankle: self.interpolate(current_joints.front_right_ankle, target_joints.front_right_ankle, progress),
                rear_left_hip: self.interpolate(current_joints.rear_left_hip, target_joints.rear_left_hip, progress),
                rear_left_knee: self.interpolate(current_joints.rear_left_knee, target_joints.rear_left_knee, progress),
                rear_left_ankle: self.interpolate(current_joints.rear_left_ankle, target_joints.rear_left_ankle, progress),
                rear_right_hip: self.interpolate(current_joints.rear_right_hip, target_joints.rear_right_hip, progress),
                rear_right_knee: self.interpolate(current_joints.rear_right_knee, target_joints.rear_right_knee, progress),
                rear_right_ankle: self.interpolate(current_joints.rear_right_ankle, target_joints.rear_right_ankle, progress),
            };
            
            self.send_joint_positions(interpolated_joints).await?;
            
            tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
        }
        
        // Send final positions
        self.send_joint_positions(target_joints).await?;
        Ok(())
    }
    
    /// Execute walking gait
    pub async fn execute_walking_gait(&mut self, steps: u32, step_length: f64, step_height: f64) -> Result<()> {
        for step in 0..steps {
            // Lift phase
            let lift_joints = self.create_step_lift_joints(step_height, step % 2 == 0)?;
            let lift_command = MotionCommand {
                joint_positions: lift_joints,
                duration: std::time::Duration::from_millis(500),
                max_velocity: 1.0,
            };
            self.execute_motion(lift_command).await?;
            
            // Forward phase
            let forward_joints = self.create_step_forward_joints(step_length, step % 2 == 0)?;
            let forward_command = MotionCommand {
                joint_positions: forward_joints,
                duration: std::time::Duration::from_millis(500),
                max_velocity: 1.0,
            };
            self.execute_motion(forward_command).await?;
            
            // Place phase
            let place_joints = self.create_step_place_joints(step % 2 == 0)?;
            let place_command = MotionCommand {
                joint_positions: place_joints,
                duration: std::time::Duration::from_millis(500),
                max_velocity: 1.0,
            };
            self.execute_motion(place_command).await?;
            
            tokio::time::sleep(tokio::time::Duration::from_millis(200)).await;
        }
        Ok(())
    }
    
    /// Validate joint positions against limits
    fn validate_joint_positions(&self, joints: &JointStates) -> Result<()> {
        if joints.front_left_hip.abs() > self.joint_limits.front_left_hip ||
           joints.front_left_knee.abs() > self.joint_limits.front_left_knee ||
           joints.front_left_ankle.abs() > self.joint_limits.front_left_ankle ||
           joints.front_right_hip.abs() > self.joint_limits.front_right_hip ||
           joints.front_right_knee.abs() > self.joint_limits.front_right_knee ||
           joints.front_right_ankle.abs() > self.joint_limits.front_right_ankle ||
           joints.rear_left_hip.abs() > self.joint_limits.rear_left_hip ||
           joints.rear_left_knee.abs() > self.joint_limits.rear_left_knee ||
           joints.rear_left_ankle.abs() > self.joint_limits.rear_left_ankle ||
           joints.rear_right_hip.abs() > self.joint_limits.rear_right_hip ||
           joints.rear_right_knee.abs() > self.joint_limits.rear_right_knee ||
           joints.rear_right_ankle.abs() > self.joint_limits.rear_right_ankle {
            return Err(anyhow::anyhow!("Joint position exceeds limits"));
        }
        Ok(())
    }
    
    /// Linear interpolation between two values
    fn interpolate(&self, start: f64, end: f64, progress: f64) -> f64 {
        start + (end - start) * progress
    }
    
    /// Create joint positions for step lift phase
    fn create_step_lift_joints(&self, height: f64, is_left_step: bool) -> Result<JointStates> {
        let mut joints = JointStates::default();
        
        if is_left_step {
            joints.front_left_knee = height;
            joints.rear_left_knee = height;
        } else {
            joints.front_right_knee = height;
            joints.rear_right_knee = height;
        }
        
        Ok(joints)
    }
    
    /// Create joint positions for step forward phase
    fn create_step_forward_joints(&self, length: f64, is_left_step: bool) -> Result<JointStates> {
        let mut joints = JointStates::default();
        
        if is_left_step {
            joints.front_left_hip = length;
            joints.rear_left_hip = length;
        } else {
            joints.front_right_hip = length;
            joints.rear_right_hip = length;
        }
        
        Ok(joints)
    }
    
    /// Create joint positions for step place phase
    fn create_step_place_joints(&self, is_left_step: bool) -> Result<JointStates> {
        // Return to neutral position
        Ok(JointStates::default())
    }
}

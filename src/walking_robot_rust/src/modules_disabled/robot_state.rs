//! Robot state management module

use serde::{Deserialize, Serialize};
use std::f64::consts::PI;

/// Robot joint states
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JointStates {
    pub front_left_hip: f64,
    pub front_left_knee: f64,
    pub front_left_ankle: f64,
    pub front_right_hip: f64,
    pub front_right_knee: f64,
    pub front_right_ankle: f64,
    pub rear_left_hip: f64,
    pub rear_left_knee: f64,
    pub rear_left_ankle: f64,
    pub rear_right_hip: f64,
    pub rear_right_knee: f64,
    pub rear_right_ankle: f64,
}

impl Default for JointStates {
    fn default() -> Self {
        Self {
            front_left_hip: 0.0,
            front_left_knee: 0.0,
            front_left_ankle: 0.0,
            front_right_hip: 0.0,
            front_right_knee: 0.0,
            front_right_ankle: 0.0,
            rear_left_hip: 0.0,
            rear_left_knee: 0.0,
            rear_left_ankle: 0.0,
            rear_right_hip: 0.0,
            rear_right_knee: 0.0,
            rear_right_ankle: 0.0,
        }
    }
}

/// Robot pose and orientation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RobotPose {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub roll: f64,
    pub pitch: f64,
    pub yaw: f64,
}

impl Default for RobotPose {
    fn default() -> Self {
        Self {
            x: 0.0,
            y: 0.0,
            z: 0.5, // Default height
            roll: 0.0,
            pitch: 0.0,
            yaw: 0.0,
        }
    }
}

/// Robot velocity state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RobotVelocity {
    pub linear_x: f64,
    pub linear_y: f64,
    pub linear_z: f64,
    pub angular_x: f64,
    pub angular_y: f64,
    pub angular_z: f64,
}

impl Default for RobotVelocity {
    fn default() -> Self {
        Self {
            linear_x: 0.0,
            linear_y: 0.0,
            linear_z: 0.0,
            angular_x: 0.0,
            angular_y: 0.0,
            angular_z: 0.0,
        }
    }
}

/// Complete robot state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RobotState {
    pub joints: JointStates,
    pub pose: RobotPose,
    pub velocity: RobotVelocity,
    pub timestamp: std::time::SystemTime,
    pub is_stable: bool,
    pub gait_phase: GaitPhase,
}

/// Gait phases for walking
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum GaitPhase {
    Stance,
    Swing,
    Transition,
}

impl Default for GaitPhase {
    fn default() -> Self {
        GaitPhase::Stance
    }
}

impl RobotState {
    /// Create a new robot state with default values
    pub fn new() -> Self {
        Self {
            joints: JointStates::default(),
            pose: RobotPose::default(),
            velocity: RobotVelocity::default(),
            timestamp: std::time::SystemTime::now(),
            is_stable: true,
            gait_phase: GaitPhase::default(),
        }
    }
    
    /// Update the robot state with new sensor data
    pub fn update(&mut self, joint_states: JointStates, pose: RobotPose, velocity: RobotVelocity) {
        self.joints = joint_states;
        self.pose = pose;
        self.velocity = velocity;
        self.timestamp = std::time::SystemTime::now();
        self.check_stability();
    }
    
    /// Check if the robot is in a stable configuration
    pub fn check_stability(&mut self) {
        // Simple stability check based on center of mass and support polygon
        let hip_sum = self.joints.front_left_hip + self.joints.front_right_hip + 
                     self.joints.rear_left_hip + self.joints.rear_right_hip;
        
        self.is_stable = hip_sum.abs() < PI / 4.0 && // Hip angles not too extreme
                        self.pose.pitch.abs() < PI / 6.0 && // Pitch not too steep
                        self.pose.roll.abs() < PI / 6.0; // Roll not too steep
    }
    
    /// Get the current gait phase based on joint positions
    pub fn get_gait_phase(&self) -> &GaitPhase {
        &self.gait_phase
    }
    
    /// Update gait phase
    pub fn update_gait_phase(&mut self, phase: GaitPhase) {
        self.gait_phase = phase;
    }
    
    /// Get joint limits for safety checking
    pub fn get_joint_limits() -> JointStates {
        JointStates {
            front_left_hip: PI / 2.0,
            front_left_knee: PI / 2.0,
            front_left_ankle: PI / 4.0,
            front_right_hip: PI / 2.0,
            front_right_knee: PI / 2.0,
            front_right_ankle: PI / 4.0,
            rear_left_hip: PI / 2.0,
            rear_left_knee: PI / 2.0,
            rear_left_ankle: PI / 4.0,
            rear_right_hip: PI / 2.0,
            rear_right_knee: PI / 2.0,
            rear_right_ankle: PI / 4.0,
        }
    }
}

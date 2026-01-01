//! Motion planning module

use anyhow::Result;
use crate::robot_state::{JointStates, RobotState, GaitPhase};
use std::f64::consts::PI;

/// Motion plan for robot movement
#[derive(Debug, Clone)]
pub struct MotionPlan {
    pub sequence: Vec<MotionCommand>,
    pub duration: std::time::Duration,
    pub plan_type: PlanType,
}

/// Individual motion command
#[derive(Debug, Clone)]
pub struct MotionCommand {
    pub target_joints: JointStates,
    pub timestamp: std::time::SystemTime,
    pub velocity_profile: VelocityProfile,
}

/// Velocity profile for smooth motion
#[derive(Debug, Clone)]
pub enum VelocityProfile {
    Constant { velocity: f64 },
    Trapezoidal { max_velocity: f64, acceleration: f64, deceleration: f64 },
    Sinusoidal { amplitude: f64, frequency: f64 },
}

/// Types of motion plans
#[derive(Debug, Clone)]
pub enum PlanType {
    StandUp,
    Walk { steps: u32, step_length: f64, step_height: f64 },
    Turn { angle: f64, radius: f64 },
    SitDown,
    Custom,
}

/// Motion planner for generating robot movements
pub struct MotionPlanner {
    current_gait_phase: GaitPhase,
    step_counter: u32,
}

impl MotionPlanner {
    /// Create a new motion planner
    pub fn new() -> Self {
        Self {
            current_gait_phase: GaitPhase::Stance,
            step_counter: 0,
        }
    }
    
    /// Plan motion based on current robot state
    pub fn plan_motion(&mut self, state: &RobotState) -> Result<MotionPlan> {
        // Default behavior: maintain stability
        if !state.is_stable {
            return self.plan_stabilization(state);
        }
        
        // Check if we need to transition gait phase
        self.update_gait_phase(state);
        
        match self.current_gait_phase {
            GaitPhase::Stance => self.plan_stance_phase(state),
            GaitPhase::Swing => self.plan_swing_phase(state),
            GaitPhase::Transition => self.plan_transition_phase(state),
        }
    }
    
    /// Plan walking motion
    pub fn plan_walking(&mut self, steps: u32, step_length: f64, step_height: f64) -> Result<MotionPlan> {
        let mut sequence = Vec::new();
        let start_time = std::time::SystemTime::now();
        
        for step in 0..steps {
            let is_left_step = step % 2 == 0;
            
            // Lift phase
            let lift_command = self.create_lift_command(step_height, is_left_step, start_time, step)?;
            sequence.push(lift_command);
            
            // Swing phase
            let swing_command = self.create_swing_command(step_length, is_left_step, start_time, step)?;
            sequence.push(swing_command);
            
            // Place phase
            let place_command = self.create_place_command(is_left_step, start_time, step)?;
            sequence.push(place_command);
        }
        
        let total_duration = std::time::Duration::from_millis(steps * 1500); // 1.5s per step
        
        Ok(MotionPlan {
            sequence,
            duration: total_duration,
            plan_type: PlanType::Walk { steps, step_length, step_height },
        })
    }
    
    /// Plan standing up motion
    pub fn plan_stand_up(&mut self) -> Result<MotionPlan> {
        let mut sequence = Vec::new();
        let start_time = std::time::SystemTime::now();
        
        // Phase 1: Prepare to stand (adjust hips)
        let prepare_joints = JointStates {
            front_left_hip: -PI / 6.0,
            front_right_hip: -PI / 6.0,
            rear_left_hip: -PI / 6.0,
            rear_right_hip: -PI / 6.0,
            ..Default::default()
        };
        
        sequence.push(MotionCommand {
            target_joints: prepare_joints,
            timestamp: start_time,
            velocity_profile: VelocityProfile::Trapezoidal {
                max_velocity: 0.5,
                acceleration: 0.2,
                deceleration: 0.2,
            },
        });
        
        // Phase 2: Extend legs
        let extend_time = start_time + std::time::Duration::from_millis(1000);
        let extend_joints = JointStates {
            front_left_hip: 0.0,
            front_left_knee: PI / 8.0,
            front_right_hip: 0.0,
            front_right_knee: PI / 8.0,
            rear_left_hip: 0.0,
            rear_left_knee: PI / 8.0,
            rear_right_hip: 0.0,
            rear_right_knee: PI / 8.0,
            ..Default::default()
        };
        
        sequence.push(MotionCommand {
            target_joints: extend_joints,
            timestamp: extend_time,
            velocity_profile: VelocityProfile::Trapezoidal {
                max_velocity: 0.3,
                acceleration: 0.1,
                deceleration: 0.1,
            },
        });
        
        // Phase 3: Final standing position
        let final_time = start_time + std::time::Duration::from_millis(2000);
        let final_joints = JointStates::default();
        
        sequence.push(MotionCommand {
            target_joints: final_joints,
            timestamp: final_time,
            velocity_profile: VelocityProfile::Sinusoidal {
                amplitude: 0.1,
                frequency: 0.5,
            },
        });
        
        Ok(MotionPlan {
            sequence,
            duration: std::time::Duration::from_millis(3000),
            plan_type: PlanType::StandUp,
        })
    }
    
    /// Plan turning motion
    pub fn plan_turn(&mut self, angle: f64, radius: f64) -> Result<MotionPlan> {
        let mut sequence = Vec::new();
        let start_time = std::time::SystemTime::now();
        
        // Calculate differential joint angles for turning
        let left_joint_offset = angle * radius / 2.0;
        let right_joint_offset = -angle * radius / 2.0;
        
        let turn_joints = JointStates {
            front_left_hip: left_joint_offset,
            rear_left_hip: left_joint_offset,
            front_right_hip: right_joint_offset,
            rear_right_hip: right_joint_offset,
            ..Default::default()
        };
        
        sequence.push(MotionCommand {
            target_joints: turn_joints,
            timestamp: start_time,
            velocity_profile: VelocityProfile::Trapezoidal {
                max_velocity: 0.4,
                acceleration: 0.2,
                deceleration: 0.2,
            },
        });
        
        Ok(MotionPlan {
            sequence,
            duration: std::time::Duration::from_millis(2000),
            plan_type: PlanType::Turn { angle, radius },
        })
    }
    
    /// Update gait phase based on current state
    fn update_gait_phase(&mut self, state: &RobotState) {
        match self.current_gait_phase {
            GaitPhase::Stance => {
                // Check if we should transition to swing
                if self.should_start_swing(state) {
                    self.current_gait_phase = GaitPhase::Transition;
                }
            }
            GaitPhase::Swing => {
                // Check if we should transition back to stance
                if self.should_end_swing(state) {
                    self.current_gait_phase = GaitPhase::Transition;
                }
            }
            GaitPhase::Transition => {
                // Complete the transition
                self.step_counter += 1;
                match self.step_counter % 2 {
                    0 => self.current_gait_phase = GaitPhase::Stance,
                    _ => self.current_gait_phase = GaitPhase::Swing,
                }
            }
        }
    }
    
    /// Check if robot should start swing phase
    fn should_start_swing(&self, state: &RobotState) -> bool {
        // Simple heuristic: start swing when robot is stable and ready
        state.is_stable && self.step_counter % 2 == 0
    }
    
    /// Check if robot should end swing phase
    fn should_end_swing(&self, state: &RobotState) -> bool {
        // Simple heuristic: end swing when leg is in target position
        state.is_stable && self.step_counter % 2 == 1
    }
    
    /// Plan stance phase motion
    fn plan_stance_phase(&mut self, state: &RobotState) -> Result<MotionPlan> {
        let sequence = vec![MotionCommand {
            target_joints: state.joints.clone(),
            timestamp: std::time::SystemTime::now(),
            velocity_profile: VelocityProfile::Constant { velocity: 0.0 },
        }];
        
        Ok(MotionPlan {
            sequence,
            duration: std::time::Duration::from_millis(100),
            plan_type: PlanType::Custom,
        })
    }
    
    /// Plan swing phase motion
    fn plan_swing_phase(&mut self, state: &RobotState) -> Result<MotionPlan> {
        let mut swing_joints = state.joints.clone();
        
        // Lift the swinging leg
        if self.step_counter % 2 == 0 {
            swing_joints.front_left_knee = PI / 6.0;
            swing_joints.rear_left_knee = PI / 6.0;
        } else {
            swing_joints.front_right_knee = PI / 6.0;
            swing_joints.rear_right_knee = PI / 6.0;
        }
        
        let sequence = vec![MotionCommand {
            target_joints: swing_joints,
            timestamp: std::time::SystemTime::now(),
            velocity_profile: VelocityProfile::Sinusoidal {
                amplitude: 0.2,
                frequency: 1.0,
            },
        }];
        
        Ok(MotionPlan {
            sequence,
            duration: std::time::Duration::from_millis(500),
            plan_type: PlanType::Custom,
        })
    }
    
    /// Plan transition phase motion
    fn plan_transition_phase(&mut self, state: &RobotState) -> Result<MotionPlan> {
        let sequence = vec![MotionCommand {
            target_joints: state.joints.clone(),
            timestamp: std::time::SystemTime::now(),
            velocity_profile: VelocityProfile::Trapezoidal {
                max_velocity: 0.1,
                acceleration: 0.05,
                deceleration: 0.05,
            },
        }];
        
        Ok(MotionPlan {
            sequence,
            duration: std::time::Duration::from_millis(200),
            plan_type: PlanType::Custom,
        })
    }
    
    /// Plan stabilization motion
    fn plan_stabilization(&mut self, state: &RobotState) -> Result<MotionPlan> {
        let mut stabilizing_joints = state.joints.clone();
        
        // Adjust joints to improve stability
        if state.pose.pitch > 0.1 {
            stabilizing_joints.front_left_hip -= 0.05;
            stabilizing_joints.front_right_hip -= 0.05;
            stabilizing_joints.rear_left_hip += 0.05;
            stabilizing_joints.rear_right_hip += 0.05;
        } else if state.pose.pitch < -0.1 {
            stabilizing_joints.front_left_hip += 0.05;
            stabilizing_joints.front_right_hip += 0.05;
            stabilizing_joints.rear_left_hip -= 0.05;
            stabilizing_joints.rear_right_hip -= 0.05;
        }
        
        let sequence = vec![MotionCommand {
            target_joints: stabilizing_joints,
            timestamp: std::time::SystemTime::now(),
            velocity_profile: VelocityProfile::Constant { velocity: 0.1 },
        }];
        
        Ok(MotionPlan {
            sequence,
            duration: std::time::Duration::from_millis(300),
            plan_type: PlanType::Custom,
        })
    }
    
    /// Create lift command for walking
    fn create_lift_command(&self, height: f64, is_left: bool, start_time: std::time::SystemTime, step: u32) -> Result<MotionCommand> {
        let mut joints = JointStates::default();
        
        if is_left {
            joints.front_left_knee = height;
            joints.rear_left_knee = height;
        } else {
            joints.front_right_knee = height;
            joints.rear_right_knee = height;
        }
        
        Ok(MotionCommand {
            target_joints: joints,
            timestamp: start_time + std::time::Duration::from_millis(step as u64 * 1500),
            velocity_profile: VelocityProfile::Sinusoidal {
                amplitude: height,
                frequency: 2.0,
            },
        })
    }
    
    /// Create swing command for walking
    fn create_swing_command(&self, length: f64, is_left: bool, start_time: std::time::SystemTime, step: u32) -> Result<MotionCommand> {
        let mut joints = JointStates::default();
        
        if is_left {
            joints.front_left_hip = length;
            joints.rear_left_hip = length;
            joints.front_left_knee = length / 2.0;
            joints.rear_left_knee = length / 2.0;
        } else {
            joints.front_right_hip = length;
            joints.rear_right_hip = length;
            joints.front_right_knee = length / 2.0;
            joints.rear_right_knee = length / 2.0;
        }
        
        Ok(MotionCommand {
            target_joints: joints,
            timestamp: start_time + std::time::Duration::from_millis(step as u64 * 1500 + 500),
            velocity_profile: VelocityProfile::Trapezoidal {
                max_velocity: 0.5,
                acceleration: 0.3,
                deceleration: 0.3,
            },
        })
    }
    
    /// Create place command for walking
    fn create_place_command(&self, is_left: bool, start_time: std::time::SystemTime, step: u32) -> Result<MotionCommand> {
        let joints = JointStates::default();
        
        Ok(MotionCommand {
            target_joints: joints,
            timestamp: start_time + std::time::Duration::from_millis(step as u64 * 1500 + 1000),
            velocity_profile: VelocityProfile::Constant { velocity: 0.2 },
        })
    }
}

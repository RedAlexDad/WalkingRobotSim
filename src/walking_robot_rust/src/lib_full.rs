//! Walking Robot Rust Library
//! 
//! This library provides core functionality for controlling and monitoring
//! a walking robot using Rust and ROS2 Jazzy.

use r2r::*;
use anyhow::Result;
use std::sync::Arc;
use tokio::sync::Mutex;

pub mod robot_controller;
pub mod robot_monitor;
pub mod robot_state;
pub mod motion_planning;

pub use robot_controller::RobotController;
pub use robot_monitor::RobotMonitor;
pub use robot_state::RobotState;
pub use motion_planning::MotionPlanner;

/// Main robot control structure
pub struct WalkingRobot {
    controller: Arc<Mutex<RobotController>>,
    monitor: Arc<Mutex<RobotMonitor>>,
    state: Arc<Mutex<RobotState>>,
    planner: Arc<Mutex<MotionPlanner>>,
}

impl WalkingRobot {
    /// Create a new walking robot instance
    pub async fn new() -> Result<Self> {
        let ctx = r2r::Context::create()?;
        
        let controller = Arc::new(Mutex::new(RobotController::new(&ctx)?));
        let monitor = Arc::new(Mutex::new(RobotMonitor::new(&ctx)?));
        let state = Arc::new(Mutex::new(RobotState::new()));
        let planner = Arc::new(Mutex::new(MotionPlanner::new()));
        
        Ok(Self {
            controller,
            monitor,
            state,
            planner,
        })
    }
    
    /// Initialize the robot system
    pub async fn initialize(&mut self) -> Result<()> {
        self.controller.lock().await.initialize().await?;
        self.monitor.lock().await.start_monitoring().await?;
        Ok(())
    }
    
    /// Main control loop
    pub async fn run(&mut self) -> Result<()> {
        loop {
            // Update robot state
            let state_update = self.monitor.lock().await.get_latest_state().await?;
            self.state.lock().await.update(state_update);
            
            // Plan next motion
            let current_state = self.state.lock().await.clone();
            let motion_plan = self.planner.lock().await.plan_motion(&current_state)?;
            
            // Execute motion
            self.controller.lock().await.execute_motion(motion_plan).await?;
            
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_robot_creation() {
        let robot = WalkingRobot::new().await;
        assert!(robot.is_ok());
    }
}

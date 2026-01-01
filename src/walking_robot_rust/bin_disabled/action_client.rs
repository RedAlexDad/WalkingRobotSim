//! Simple action client for testing ROS2 actions

use r2r::*;
use anyhow::Result;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize ROS2 context
    let ctx = r2r::Context::create()?;
    
    // Create action client
    let client = ctx.create_action_client::<r2r::example_interfaces::action::Fibonacci>("/fibonacci_action")?;
    
    println!("🎯 Action client ready");
    
    // Wait for action server to be available
    while !client.is_available()? {
        println!("⏳ Waiting for action server...");
        tokio::time::sleep(Duration::from_secs(1)).await;
    }
    
    let mut counter = 0;
    loop {
        // Create goal
        let goal = r2r::example_interfaces::action::Fibonacci::Goal {
            order: 10 + counter % 5,
        };
        
        println!("📤 Sending action goal: order={}", goal.order);
        
        // Send goal and wait for result
        match client.send_goal(goal).await? {
            result => {
                println!("📨 Action result: sequence={:?}", result.sequence);
            }
        }
        
        counter += 1;
        tokio::time::sleep(Duration::from_secs(10)).await;
    }
}

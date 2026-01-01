//! Simple action server for testing ROS2 actions

use r2r::*;
use anyhow::Result;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize ROS2 context
    let ctx = r2r::Context::create()?;
    
    // Create action server
    let action_server = ctx.create_action_server::<r2r::example_interfaces::action::Fibonacci, _>(
        "/fibonacci_action",
        |goal| async move {
            println!("🎯 Action goal received: order={}", goal.order);
            
            // Accept the goal
            let mut sequence = vec![0, 1];
            
            for i in 2..goal.order {
                let next_val = sequence[i-1] + sequence[i-2];
                sequence.push(next_val);
                
                // Send feedback
                let feedback = r2r::example_interfaces::action::Fibonacci::Feedback {
                    partial_sequence: sequence.clone(),
                };
                
                println!("📊 Feedback: sequence={:?}", sequence);
                // In a real implementation, you would send feedback here
                
                tokio::time::sleep(Duration::from_millis(500)).await;
            }
            
            // Send result
            let result = r2r::example_interfaces::action::Fibonacci::Result {
                sequence,
            };
            
            println!("✅ Action completed!");
            Ok(result)
        },
    )?;
    
    println!("🎯 Action server ready on /fibonacci_action");
    
    // Keep the action server running
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    }
}

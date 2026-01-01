//! Simple message sender for testing ROS2 communication

use r2r::*;
use anyhow::Result;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize ROS2 context
    let ctx = r2r::Context::create()?;
    
    // Create publisher for string messages
    let publisher = ctx.create_publisher::<r2r::std_msgs::msg::String>(
        "/test_topic",
        r2r::QosProfile::default(),
    )?;
    
    // Create publisher for geometry messages
    let twist_publisher = ctx.create_publisher::<r2r::geometry_msgs::msg::Twist>(
        "/cmd_vel",
        r2r::QosProfile::default(),
    )?;
    
    println!("🚀 Starting message sender...");
    
    let mut counter = 0;
    loop {
        // Send string message
        let mut string_msg = r2r::std_msgs::msg::String::default();
        string_msg.data = format!("Hello from Rust! Message #{}", counter);
        
        publisher.publish(&string_msg)?;
        println!("📤 Sent: {}", string_msg.data);
        
        // Send twist command every 5 messages
        if counter % 5 == 0 {
            let mut twist_msg = r2r::geometry_msgs::msg::Twist::default();
            twist_msg.linear.x = 0.5;
            twist_msg.angular.z = 0.2;
            
            twist_publisher.publish(&twist_msg)?;
            println!("📤 Sent velocity command: linear_x=0.5, angular_z=0.2");
        }
        
        counter += 1;
        tokio::time::sleep(Duration::from_secs(1)).await;
    }
}

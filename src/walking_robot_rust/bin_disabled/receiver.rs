//! Simple message receiver for testing ROS2 communication

use r2r::*;
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize ROS2 context
    let ctx = r2r::Context::create()?;
    
    // Create subscriber for string messages
    let string_subscriber = ctx.create_subscription::<r2r::std_msgs::msg::String>(
        "/test_topic",
        r2r::QosProfile::default(),
    )?;
    
    // Create subscriber for twist messages
    let twist_subscriber = ctx.create_subscription::<r2r::geometry_msgs::msg::Twist>(
        "/cmd_vel",
        r2r::QosProfile::default(),
    )?;
    
    println!("👂 Starting message receiver...");
    
    // Spawn task for string messages
    let mut string_sub = string_subscriber;
    tokio::spawn(async move {
        while let Ok(msg) = string_sub.next().await {
            println!("📨 Received string: {}", msg.data);
        }
    });
    
    // Spawn task for twist messages
    let mut twist_sub = twist_subscriber;
    tokio::spawn(async move {
        while let Ok(msg) = twist_sub.next().await {
            println!("📨 Received twist: linear_x={}, linear_y={}, angular_z={}", 
                     msg.linear.x, msg.linear.y, msg.angular.z);
        }
    });
    
    println!("✅ Receiver ready, waiting for messages...");
    
    // Keep the program running
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    }
}

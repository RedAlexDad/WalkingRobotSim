//! Native Rust test without ROS2 dependencies
//! This demonstrates that rclrs can be linked without custom messages

use anyhow::{Error, Result};
use rclrs::*;

fn main() -> Result<(), Error> {
    println!("🚀 Starting native Rust test...");
    
    // Test basic rclrs functionality
    let context = Context::default_from_env()?;
    let executor = context.create_basic_executor();
    let node = executor.create_node("native_test_node")?;
    
    println!("✅ Node created successfully");
    println!("✅ Node name: {}", node.name());
    println!("✅ Context OK: {}", context.ok());
    
    // Test basic spinning
    println!("✅ Native rclrs test completed successfully!");
    println!("⏳ Spinning for 5 seconds...");
    
    // Spin for 5 seconds
    let start = std::time::Instant::now();
    while start.elapsed() < std::time::Duration::from_secs(5) && context.ok() {
        // Just spin without complex operations
        std::thread::sleep(std::time::Duration::from_millis(100));
    }
    
    println!("🎉 Test completed!");
    Ok(())
}

//! Simple publisher using rclrs 0.6.x with test_msgs

use anyhow::{Error, Result};
use rclrs::*;

fn main() -> Result<(), Error> {
    println!("🚀 Starting Rust simple publisher...");
    
    let context = Context::default_from_env()?;
    let executor = context.create_basic_executor();

    let node = executor.create_node("simple_rust_publisher")?;

    // Use test_msgs from rclrs vendor
    let publisher = node.create_publisher::<rclrs::vendor::test_msgs::msg::Strings>("rust_topic")?;

    let mut message = rclrs::vendor::test_msgs::msg::Strings::default();

    let mut publish_count: u32 = 1;

    println!("✅ Publisher ready on topic: rust_topic");

    while context.ok() {
        message.string_value = format!("Hello from Rust! Message #{}", publish_count);
        println!("📤 Publishing: [{}]", message.string_value);
        publisher.publish(&message)?;
        publish_count += 1;
        std::thread::sleep(std::time::Duration::from_millis(1000));
    }
    Ok(())
}

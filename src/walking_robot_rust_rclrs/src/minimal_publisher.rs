//! Minimal publisher using rclrs 0.6.x

use anyhow::{Error, Result};
use rclrs::*;

fn main() -> Result<(), Error> {
    println!("🚀 Starting Rust minimal publisher...");
    
    let context = Context::default_from_env()?;
    let executor = context.create_basic_executor();

    let node = executor.create_node("minimal_rust_publisher")?;

    let publisher = node.create_publisher::<example_interfaces::msg::String>("rust_topic")?;

    let mut message = example_interfaces::msg::String::default();

    let mut publish_count: u32 = 1;

    println!("✅ Publisher ready on topic: rust_topic");

    while context.ok() {
        message.data = format!("Hello from Rust! Message #{}", publish_count);
        println!("📤 Publishing: [{}]", message.data);
        publisher.publish(&message)?;
        publish_count += 1;
        std::thread::sleep(std::time::Duration::from_millis(1000));
    }
    Ok(())
}

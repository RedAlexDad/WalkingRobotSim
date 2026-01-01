//! Minimal subscriber using rclrs 0.6.x

use anyhow::{Error, Result};
use rclrs::*;

fn main() -> Result<(), Error> {
    println!("👂 Starting Rust minimal subscriber...");
    
    let context = Context::default_from_env()?;
    let mut executor = context.create_basic_executor();

    let node = executor.create_node("minimal_rust_subscriber")?;

    let worker = node.create_worker::<usize>(0);
    let _subscription = worker.create_subscription::<example_interfaces::msg::String, _>(
        "rust_topic",
        move |num_messages: &mut usize, msg: example_interfaces::msg::String| {
            *num_messages += 1;
            println!("📨 #{} | I heard: '{}'", *num_messages, msg.data);
        },
    )?;

    println!("✅ Subscriber ready on topic: rust_topic");
    println!("⏳ Waiting for messages...");
    
    executor.spin(SpinOptions::default()).first_error()?;
    Ok(())
}

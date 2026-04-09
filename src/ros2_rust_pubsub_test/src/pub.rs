//! ROS 2 Rust Publisher
//! Терминал 1: ros2 run ros2_rust_pubsub_test pub

use rclrs::{Context, CreateBasicExecutor, Publisher, PublisherOptions};
use rclrs::vendor::example_interfaces::msg::String;
use std::time::Duration;

fn main() {
    println!("🦀 Publisher starting...");
    println!("   Node: rust_pub");
    println!("   Topic: test_topic\n");

    let ctx = Context::default_from_env().expect("Failed to init context");
    let mut executor = ctx.create_basic_executor();
    let node = executor
        .commands()
        .create_node("rust_pub")
        .expect("Failed to create node");

    println!("✅ Node created");

    let publisher: Publisher<String> = node
        .create_publisher(PublisherOptions::new("test_topic"))
        .expect("Failed to create publisher");
    println!("✅ Publisher created on test_topic");
    println!("⏳ Waiting 2s for subscribers...\n");
    std::thread::sleep(Duration::from_secs(2));

    println!("📡 Publishing 10 messages (500ms interval):\n");
    for i in 1..=10 {
        let mut msg = String::default();
        msg.data = format!("Hello #{}", i);
        publisher.publish(&msg).expect("Failed to publish");
        println!("  📤 [{}] Hello #{}", i, i);
        std::thread::sleep(Duration::from_millis(500));
    }

    println!("\n✅ Done! Published 10 messages.");
}

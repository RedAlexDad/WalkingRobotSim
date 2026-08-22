//! ROS 2 Rust Subscriber
//! Терминал 2: ros2 run ros2_rust_pubsub_test sub

use rclrs::{Context, CreateBasicExecutor, SpinOptions, Subscription, SubscriptionOptions};
use rclrs::vendor::example_interfaces::msg::String;
use std::sync::{Arc, Mutex};
use std::time::Duration;

fn main() {
    println!("🦀 Subscriber starting...");
    println!("   Node: rust_sub");
    println!("   Topic: test_topic\n");

    let ctx = Context::default_from_env().expect("Failed to init context");
    let mut executor = ctx.create_basic_executor();
    let node = executor
        .commands()
        .create_node("rust_sub")
        .expect("Failed to create node");

    println!("✅ Node created");

    let count = Arc::new(Mutex::new(0u32));
    let count_clone = count.clone();

    let _sub: Subscription<String> = node
        .create_subscription(
            SubscriptionOptions::new("test_topic"),
            move |msg: String| {
                let mut c = count_clone.lock().unwrap();
                *c += 1;
                println!("  📩 [{}] Received: {}", *c, msg.data);
            },
        )
        .expect("Failed to create subscription");
    println!("✅ Subscribed to test_topic");
    println!("⏰ Listening for 15s...\n");

    // Spin for 15 seconds — callbacks are called during this time
    let mut spin_opts = SpinOptions::new();
    spin_opts.timeout = Some(Duration::from_secs(15));
    executor.spin(spin_opts);

    let final_count = *count.lock().unwrap();
    println!("\n✅ Total received: {} messages", final_count);
}

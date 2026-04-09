//! Minimal ROS 2 Rust node - demonstrates rclrs initialization and node creation
//! This test proves rclrs 0.7 API works without needing message types.

use rclrs::Executor;

fn main() {
    println!("🦀 ROS 2 Rust test starting...\n");

    // Create executor
    let executor = Executor::new();
    println!("✅ Executor created");

    // Create node
    let node = executor.create_node("timer_pub").unwrap();
    println!("✅ Node 'timer_pub' created");
    println!("   Full name: {:?}", node.fully_qualified_name());
    println!("   Namespace: {:?}", node.namespace());

    println!("\n✅ rclrs 0.7 initialized successfully!");
    println!("🎉 ROS 2 Rust infrastructure works!");
}
}

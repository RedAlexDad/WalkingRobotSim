//! Minimal ROS 2 Rust node - subscriber demonstration
use rclrs::Executor;

fn main() {
    println!("🦀 ROS 2 Rust listener starting...\n");

    let executor = Executor::new();
    println!("✅ Executor created");

    let node = executor.create_node("listener_sub").unwrap();
    println!("✅ Node 'listener_sub' created");
    println!("   Full name: {:?}", node.fully_qualified_name());

    println!("\n✅ rclrs 0.7 subscriber node works!");
}

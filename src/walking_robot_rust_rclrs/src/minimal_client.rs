//! Minimal service client using rclrs

use rclrs::Context;
use example_interfaces::srv::AddTwoInts;
use std::time::Duration;

fn main() -> Result<(), rclrs::RclError> {
    println!("🔌 Starting Rust minimal service client...");
    
    // Create ROS2 context
    let context = Context::new()?;
    
    // Create node
    let node = context.create_node("minimal_rust_client")?;
    
    // Create service client
    let client = node.create_client::<AddTwoInts>("add_two_ints")?;
    
    println!("✅ Service client ready for: add_two_ints");
    
    // Wait for service to be available
    println!("⏳ Waiting for service to become available...");
    while !client.service_is_available() {
        std::thread::sleep(Duration::from_millis(500));
    }
    println!("✅ Service is available!");
    
    // Send requests
    let mut count = 0;
    loop {
        let request = AddTwoInts::Request {
            a: count,
            b: count + 1,
        };
        
        println!("📤 Sending request: {} + {}", request.a, request.b);
        
        match client.call_async(&request)?.wait() {
            Ok(response) => {
                println!("📨 Response: {} + {} = {}", request.a, request.b, response.sum);
            }
            Err(e) => {
                println!("❌ Service call failed: {:?}", e);
            }
        }
        
        count += 1;
        std::thread::sleep(Duration::from_secs(3));
    }
}

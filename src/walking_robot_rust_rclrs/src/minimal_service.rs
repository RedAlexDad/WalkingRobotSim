//! Minimal service server using rclrs

use rclrs::Context;
use example_interfaces::srv::AddTwoInts;

fn main() -> Result<(), rclrs::RclError> {
    println!("🔧 Starting Rust minimal service server...");
    
    // Create ROS2 context
    let context = Context::new()?;
    
    // Create node
    let node = context.create_node("minimal_rust_service")?;
    
    // Create service server
    let _service = node.create_service::<AddTwoInts, _>(
        "add_two_ints",
        |request: AddTwoInts::Request| -> AddTwoInts::Response {
            println!("📤 Service request: {} + {}", request.a, request.b);
            let sum = request.a + request.b;
            println!("📨 Service response: {}", sum);
            
            AddTwoInts::Response { sum }
        },
    )?;
    
    println!("✅ Service server ready on: add_two_ints");
    println!("⏳ Waiting for requests...");
    
    // Spin forever
    rclrs::spin(&node)?;
    
    Ok(())
}

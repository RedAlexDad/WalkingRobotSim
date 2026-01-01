//! Simple service server for testing ROS2 services

use r2r::*;
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize ROS2 context
    let ctx = r2r::Context::create()?;
    
    // Create service server
    let service_server = ctx.create_service_server::<r2r::std_srvs::srv::SetBool, _>(
        "/test_service",
        |req| async move {
            println!("🔧 Service request received: data={}", req.data);
            
            let mut response = r2r::std_srvs::srv::SetBool::Response::default();
            response.success = true;
            response.message = if req.data {
                "Boolean set to TRUE".to_string()
            } else {
                "Boolean set to FALSE".to_string()
            };
            
            println!("📤 Service response: success={}, message='{}'", response.success, response.message);
            Ok(response)
        },
    )?;
    
    println!("🔧 Service server ready on /test_service");
    
    // Keep the service running
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    }
}

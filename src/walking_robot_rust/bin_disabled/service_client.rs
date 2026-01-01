//! Simple service client for testing ROS2 services

use r2r::*;
use anyhow::Result;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize ROS2 context
    let ctx = r2r::Context::create()?;
    
    // Create service client
    let client = ctx.create_client::<r2r::std_srvs::srv::SetBool>("/test_service")?;
    
    println!("🔌 Service client ready");
    
    let mut counter = 0;
    loop {
        // Wait for service to be available
        while !client.is_available()? {
            println!("⏳ Waiting for service...");
            tokio::time::sleep(Duration::from_secs(1)).await;
        }
        
        // Create request
        let mut request = r2r::std_srvs::srv::SetBool::Request::default();
        request.data = counter % 2 == 0;
        
        println!("📤 Sending service request: data={}", request.data);
        
        // Send request and wait for response
        match client.call(&request).await? {
            response => {
                println!("📨 Service response: success={}, message='{}'", 
                         response.success, response.message);
            }
        }
        
        counter += 1;
        tokio::time::sleep(Duration::from_secs(3)).await;
    }
}

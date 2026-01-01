//! Temporary simple library for testing

pub fn hello_rust() -> String {
    "Hello from Rust ROS2 package!".to_string()
}

pub fn get_test_message(id: u32) -> String {
    format!("Test message #{} from Rust", id)
}

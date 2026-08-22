//! Build script to link quadropted_msgs libraries

use std::env;

fn main() {
    // Get ROS 2 install path
    let ament_prefix = env::var("AMENT_PREFIX_PATH")
        .unwrap_or_else(|_| "/opt/ros/jazzy".to_string());

    // Add library search paths
    for path in ament_prefix.split(':') {
        println!("cargo:rustc-link-search=native={}/lib", path);
    }

    // Link quadropted_msgs libraries
    println!("cargo:rustc-link-lib=dylib=quadropted_msgs__rosidl_generator_c");
    println!("cargo:rustc-link-lib=dylib=quadropted_msgs__rosidl_typesupport_c");

    // Re-run if environment changes
    println!("cargo:rerun-if-env-changed=AMENT_PREFIX_PATH");
}

//! Build script to link std_msgs libraries

use std::env;

fn main() {
    // Get ROS 2 install path
    let ament_prefix = env::var("AMENT_PREFIX_PATH")
        .unwrap_or_else(|_| "/opt/ros/jazzy".to_string());

    // Add library search path
    println!("cargo:rustc-link-search=native={}/lib", ament_prefix);

    // Link std_msgs libraries
    println!("cargo:rustc-link-lib=dylib=std_msgs__rosidl_generator_c");
    println!("cargo:rustc-link-lib=dylib=std_msgs__rosidl_typesupport_c");

    // Re-run if environment changes
    println!("cargo:rerun-if-env-changed=AMENT_PREFIX_PATH");
}

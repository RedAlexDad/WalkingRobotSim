//! Build script to link visualization_msgs libraries

use std::env;

fn main() {
    let ament_prefix = env::var("AMENT_PREFIX_PATH").unwrap_or_else(|_| "/opt/ros/jazzy".to_string());

    for path in ament_prefix.split(':') {
        println!("cargo:rustc-link-search=native={}/lib", path);
    }

    println!("cargo:rustc-link-lib=dylib=visualization_msgs__rosidl_generator_c");
    println!("cargo:rustc-link-lib=dylib=visualization_msgs__rosidl_typesupport_c");
    // Direct FFI into sequence helpers of the message libraries used by Marker fields
    println!("cargo:rustc-link-lib=dylib=geometry_msgs__rosidl_generator_c");
    println!("cargo:rustc-link-lib=dylib=std_msgs__rosidl_generator_c");

    println!("cargo:rerun-if-env-changed=AMENT_PREFIX_PATH");
}

//! Build script to link nav_msgs libraries

use std::env;

fn main() {
    let ament_prefix = env::var("AMENT_PREFIX_PATH").unwrap_or_else(|_| "/opt/ros/jazzy".to_string());

    for path in ament_prefix.split(':') {
        println!("cargo:rustc-link-search=native={}/lib", path);
    }

    println!("cargo:rustc-link-lib=dylib=nav_msgs__rosidl_generator_c");
    println!("cargo:rustc-link-lib=dylib=nav_msgs__rosidl_typesupport_c");

    println!("cargo:rerun-if-env-changed=AMENT_PREFIX_PATH");
}

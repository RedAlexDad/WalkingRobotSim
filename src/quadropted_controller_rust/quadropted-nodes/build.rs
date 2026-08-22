//! Build script to link against ROS 2 system libraries

fn main() {
    // Get ROS 2 library paths from environment
    let ament_prefix = std::env::var("AMENT_PREFIX_PATH")
        .or_else(|_| std::env::var("ROS_DISTRO").map(|d| format!("/opt/ros/{}", d)))
        .unwrap_or_else(|_| "/opt/ros/jazzy".to_string());

    // Link geometry_msgs
    println!("cargo:rustc-link-lib=dylib=geometry_msgs__rosidl_generator_c");
    println!("cargo:rustc-link-lib=dylib=geometry_msgs__rosidl_typesupport_c");
    println!("cargo:rustc-link-search=native={}/lib", ament_prefix);

    // Re-run if environment changes
    println!("cargo:rerun-if-env-changed=AMENT_PREFIX_PATH");
}

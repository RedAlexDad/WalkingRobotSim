#!/usr/bin/env python3

"""
Build script for Rust ROS2 package
"""

import os
import sys
import subprocess
import shutil

def main():
    """Build the Rust package"""
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Building Rust package in: {package_dir}")
    
    # Change to package directory
    os.chdir(package_dir)
    
    # Check if Cargo.toml exists
    if not os.path.exists("Cargo.toml"):
        print("Error: Cargo.toml not found!")
        sys.exit(1)
    
    # Build release version
    try:
        result = subprocess.run(
            ["cargo", "build", "--release"],
            check=True,
            capture_output=True,
            text=True
        )
        print("Rust build successful!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Rust build failed: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    
    # Create target directory if it doesn't exist
    target_dir = os.path.join(package_dir, "target", "release")
    if not os.path.exists(target_dir):
        print("Error: target/release directory not found!")
        sys.exit(1)
    
    print("Build completed successfully!")

if __name__ == "__main__":
    main()

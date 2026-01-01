#!/usr/bin/env python3

"""
Runner script for Rust ROS2 nodes
"""

import os
import sys
import subprocess
import signal

def main():
    """Run a Rust node"""
    if len(sys.argv) < 2:
        print("Usage: run_rust_node.py <binary_name>")
        sys.exit(1)
    
    binary_name = sys.argv[1]
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    binary_path = os.path.join(package_dir, "target", "release", binary_name)
    
    # Check if binary exists
    if not os.path.exists(binary_path):
        print(f"Error: Binary {binary_path} not found!")
        print("Please run build_rust.py first")
        sys.exit(1)
    
    print(f"Running Rust node: {binary_name}")
    
    # Run the binary
    try:
        process = subprocess.Popen([binary_path] + sys.argv[2:])
        
        # Handle SIGINT gracefully
        def signal_handler(sig, frame):
            print("\nShutting down...")
            process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Wait for process to complete
        process.wait()
        
    except FileNotFoundError:
        print(f"Error: Could not execute {binary_path}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        if process:
            process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()

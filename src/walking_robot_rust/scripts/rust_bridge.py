#!/usr/bin/env python3

"""
Bridge between Rust binaries and ROS2
"""

import os
import sys
import json
import subprocess
import threading
import time
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.subscription import Subscription
from std_msgs.msg import String, Header
from geometry_msgs.msg import Twist

class RustBridge(Node):
    """Bridge node to connect Rust binaries with ROS2"""
    
    def __init__(self):
        super().__init__('rust_bridge')
        
        # Publishers
        self.string_publisher = self.create_publisher(String, '/test_topic', 10)
        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Subscribers
        self.string_subscriber = self.create_subscription(
            String, '/test_topic_in', self.string_callback, 10
        )
        
        # Rust process
        self.rust_process = None
        self.running = False
        
        self.get_logger().info("Rust Bridge initialized")
    
    def string_callback(self, msg):
        """Handle incoming string messages"""
        self.get_logger().info(f"Received: {msg.data}")
        
        # Send to Rust process if running
        if self.rust_process and self.rust_process.poll() is None:
            try:
                # Send message to Rust process stdin
                self.rust_process.stdin.write(f"{msg.data}\n")
                self.rust_process.stdin.flush()
            except Exception as e:
                self.get_logger().error(f"Error sending to Rust: {e}")
    
    def start_rust_process(self):
        """Start the Rust binary"""
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rust_binary = os.path.join(package_dir, 'target', 'release', 'simple_test')
        
        if not os.path.exists(rust_binary):
            self.get_logger().error(f"Rust binary not found: {rust_binary}")
            return False
        
        try:
            self.rust_process = subprocess.Popen(
                [rust_binary],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Start thread to read Rust output
            threading.Thread(target=self.read_rust_output, daemon=True).start()
            
            self.running = True
            self.get_logger().info("Rust process started")
            return True
            
        except Exception as e:
            self.get_logger().error(f"Failed to start Rust process: {e}")
            return False
    
    def read_rust_output(self):
        """Read output from Rust process and publish to ROS2"""
        while self.running and self.rust_process:
            try:
                line = self.rust_process.stdout.readline()
                if not line:
                    break
                
                # Parse JSON output from Rust
                if '"id"' in line and '"content"' in line:
                    try:
                        data = json.loads(line.strip())
                        
                        # Create ROS2 message
                        msg = String()
                        msg.data = f"Rust: {data['content']} (ID: {data['id']})"
                        
                        self.string_publisher.publish(msg)
                        self.get_logger().info(f"Published Rust message: {msg.data}")
                        
                    except json.JSONDecodeError:
                        self.get_logger().warning(f"Invalid JSON from Rust: {line}")
                
            except Exception as e:
                self.get_logger().error(f"Error reading Rust output: {e}")
                break
    
    def stop_rust_process(self):
        """Stop the Rust process"""
        self.running = False
        if self.rust_process:
            try:
                self.rust_process.terminate()
                self.rust_process.wait(timeout=5)
            except Exception as e:
                self.get_logger().error(f"Error stopping Rust process: {e}")
        
        self.get_logger().info("Rust process stopped")

def main(args=None):
    """Main function"""
    import rclpy
    
    rclpy.init(args=args)
    
    bridge = RustBridge()
    
    # Start Rust process
    if not bridge.start_rust_process():
        bridge.get_logger().error("Failed to start Rust bridge")
        rclpy.shutdown()
        return
    
    try:
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop_rust_process()
        bridge.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

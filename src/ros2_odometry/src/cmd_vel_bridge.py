#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from control_input_msgs.msg import Inputs


class CmdVelBridge(Node):
    def __init__(self):
        super().__init__("cmd_vel_bridge")
        self.sub = self.create_subscription(
            Twist, "/cmd_vel", self.cmd_vel_callback, 10
        )
        self.pub = self.create_publisher(Inputs, "/control_inputs", 10)

    def cmd_vel_callback(self, msg):
        inputs = Inputs()
        inputs.linear_x = msg.linear.x
        inputs.angular_z = msg.angular.z
        self.pub.publish(inputs)

    def main():
        rclpy.init()
        node = CmdVelBridge()
        rclpy.spin(node)
        rclpy.shutdown()

    if __name__ == "__main__":
        main()

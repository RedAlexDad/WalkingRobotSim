#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from quadropted_msgs.msg import RobotVelocity
import math


class RobotVelocityHandler(Node):
    def __init__(self):
        super().__init__("robot_velocity_handler")

        self.declare_parameter("verbose", False)
        self.verbose = self.get_parameter("verbose").get_parameter_value().bool_value
        if self.verbose:
            self.get_logger().info(f"Verbose mode: {self.verbose}")

        self.subscription = self.create_subscription(
            Twist, "cmd_vel", self.robot_velocity_callback, 10
        )

        self.publisher_ = self.create_publisher(RobotVelocity, "robot_velocity", 10)
        if self.verbose:
            self.get_logger().info("Node started: RobotVelocityHandler")

        # Переменная для секундомера
        self.motion_start_time = None

    def robot_velocity_callback(self, msg: Twist):
        # Определяем, есть ли ненулевая скорость
        has_velocity = (
            msg.linear.x != 0
            or msg.linear.y != 0
            or msg.linear.z != 0
            or msg.angular.x != 0
            or msg.angular.y != 0
            or msg.angular.z != 0
        )

        current_time = self.get_clock().now()

        # Если есть ненулевая скорость и секундомер не запущен — запускаем его
        if has_velocity and self.motion_start_time is None:
            self.motion_start_time = current_time
            if self.verbose:
                self.get_logger().info(
                    f"Motion started at time: {current_time.to_msg()}"
                )

        # Если скорости нет (робот остановился) и секундомер был запущен — останавливаем его
        if not has_velocity and self.motion_start_time is not None:
            elapsed = current_time - self.motion_start_time
            if self.verbose:
                self.get_logger().info(
                    f"Motion stopped at time: {current_time.to_msg()}"
                )
                self.get_logger().info(
                    f"Elapsed motion time: {elapsed.nanoseconds / 1e9:.3f} seconds"
                )
            self.motion_start_time = None
        if self.verbose:
            self.get_logger().info(
                f"Received Twist: linear=({msg.linear.x}, {msg.linear.y}, {msg.linear.z}), "
                f"angular=({msg.angular.x}, {msg.angular.y}, {msg.angular.z})"
            )

        new_msg = RobotVelocity()
        new_msg.robot_id = 1

        # STAND режим: линейное масштабирование чтобы speed из teleop влиял на скорость
        # TROT/CRAWL: используют насыщающую экспоненту для ограничения максимальной скорости
        # Для STAND нужно чтобы увеличение speed давало пропорциональное ускорение
        new_msg.cmd_vel.linear.x = self.linear_scale_and_limit(
            msg.linear.x, 0.035, -1.0, 1.0
        )
        new_msg.cmd_vel.linear.y = self.linear_scale_and_limit(
            msg.linear.y, 0.012, -1.0, 1.0
        )
        # linear.z (вверх/вниз) — линейное масштабирование
        new_msg.cmd_vel.linear.z = self.linear_scale_and_limit(
            msg.linear.z, 0.035, -1.0, 1.0
        )

        # angular.x/y (roll/pitch) — линейное масштабирование для STAND
        new_msg.cmd_vel.angular.x = self.linear_scale_and_limit(
            msg.angular.x, 0.1, -1.0, 1.0
        )
        new_msg.cmd_vel.angular.y = self.linear_scale_and_limit(
            msg.angular.y, 0.1, -1.0, 1.0
        )
        new_msg.cmd_vel.angular.z = self.limit(msg.angular.z, -1.0, 1.0)

        self.publisher_.publish(new_msg)
        if self.verbose:
            self.get_logger().info(
                f"Published RobotVelocity: robot_id={new_msg.robot_id}, "
                f"linear=({new_msg.cmd_vel.linear.x}, {new_msg.cmd_vel.linear.y}, {new_msg.cmd_vel.linear.z}), "
                f"angular=({new_msg.cmd_vel.angular.x}, {new_msg.cmd_vel.angular.y}, {new_msg.cmd_vel.angular.z})"
            )

    def multiply_and_limit(self, value, scale_factor, min_limit, max_limit):
        # Обработка положительных и отрицательных значений отдельно
        if value > 0:
            adjusted_value = value * 0.035
            scaled_value = scale_factor * (1 - math.exp(-100 * adjusted_value))
        else:
            # Для отрицательных значений значение умножаем на -0.035
            adjusted_value = (-value) * 0.035
            scaled_value = -scale_factor * (1 - math.exp(-100 * adjusted_value))

        return self.limit_value(scaled_value, min_limit, max_limit)

    def linear_scale_and_limit(self, value, scale_factor, min_limit, max_limit):
        # Линейное масштабирование: value * scale_factor, с ограничением
        # teleop speed=0.5 → value=0.5 → scaled=0.5*0.035=0.0175
        # teleop speed=1.0 → value=1.0 → scaled=1.0*0.035=0.035
        # teleop speed=2.0 → value=2.0 → scaled=2.0*0.035=0.07 (но ограничено max_limit=1.0)
        scaled_value = value * scale_factor
        return self.limit_value(scaled_value, min_limit, max_limit)

    def limit_value(self, value, min_limit, max_limit):
        if value > max_limit:
            return max_limit
        elif value < min_limit:
            return min_limit
        else:
            return value

    def limit(self, value, min_limit, max_limit):
        if value > max_limit:
            return max_limit
        elif value < min_limit:
            return min_limit
        else:
            return value


def main(args=None):
    rclpy.init(args=args)
    node = RobotVelocityHandler()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

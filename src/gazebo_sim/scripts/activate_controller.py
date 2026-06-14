#!/usr/bin/env python3
import rclpy
from controller_manager_msgs.srv import ListControllers, SwitchController
from rclpy.node import Node


class ControllerActivator(Node):
    def __init__(self):
        super().__init__("controller_activator")
        self.log = self.get_logger()
        self._activated = False

        self._list_cli = self.create_client(
            ListControllers, "/robot1/controller_manager/list_controllers"
        )
        self._switch_cli = self.create_client(
            SwitchController, "/robot1/controller_manager/switch_controller"
        )

    def activate(self) -> bool:
        if not self._wait_for_controller_manager():
            return False
        return self._activate_controller()

    def _wait_for_controller_manager(self) -> bool:
        if not self._list_cli.wait_for_service(timeout_sec=1.0):
            self.log.info("Waiting for controller manager...")
        self.log.info("Controller manager available")
        return True

    def _activate_controller(self) -> bool:
        import time

        for attempt in range(30):
            req = ListControllers.Request()
            fut = self._list_cli.call_async(req)
            rclpy.spin_until_future_complete(self, fut)
            ctrl_list = fut.result().controller
            names = [c.name for c in ctrl_list]
            states = {c.name: c.state for c in ctrl_list}
            self.log.info(f"Controllers: {states}")

            if (
                "joint_group_controller" in names
                and states["joint_group_controller"] == "inactive"
            ):
                req = SwitchController.Request()
                req.activate_controllers = ["joint_group_controller"]
                req.strictness = 1
                req.activate_asap = True
                req.timeout.sec = 5
                fut = self._switch_cli.call_async(req)
                rclpy.spin_until_future_complete(self, fut)
                res = fut.result()
                self.log.info(
                    f"Activation attempt {attempt + 1}: ok={res.ok} msg={res.message}"
                )
                if res.ok:
                    self._activated = True
                    return True
            elif (
                "joint_group_controller" in names
                and states["joint_group_controller"] == "active"
            ):
                self._activated = True
                return True

            time.sleep(2.0)

        return False


def main(args=None):
    rclpy.init(args=args)
    node = ControllerActivator()
    ok = node.activate()
    if ok:
        node.log.info("joint_group_controller activated successfully")
    else:
        node.log.error("Failed to activate joint_group_controller after 30 attempts")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

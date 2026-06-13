#!/usr/bin/env python3
import rclpy
from controller_manager_msgs.srv import SwitchController, ListControllers

rclpy.init()
node = rclpy.create_node("controller_activator")
log = node.get_logger()

list_cli = node.create_client(ListControllers, "/robot1/controller_manager/list_controllers")
switch_cli = node.create_client(SwitchController, "/robot1/controller_manager/switch_controller")

while not list_cli.wait_for_service(timeout_sec=1.0):
    log.info("Waiting for controller manager...")
log.info("Controller manager available")

import time
activated = False
for attempt in range(30):
    req = ListControllers.Request()
    fut = list_cli.call_async(req)
    rclpy.spin_until_future_complete(node, fut)
    ctrl_list = fut.result().controller
    names = [c.name for c in ctrl_list]
    states = {c.name: c.state for c in ctrl_list}
    log.info(f"Controllers: {states}")

    if "joint_group_controller" in names and states["joint_group_controller"] == "inactive":
        req = SwitchController.Request()
        req.activate_controllers = ["joint_group_controller"]
        req.strictness = 1
        req.activate_asap = True
        req.timeout.sec = 5
        fut = switch_cli.call_async(req)
        rclpy.spin_until_future_complete(node, fut)
        res = fut.result()
        log.info(f"Activation attempt {attempt+1}: ok={res.ok} msg={res.message}")
        if res.ok:
            activated = True
            break
    elif "joint_group_controller" in names and states["joint_group_controller"] == "active":
        activated = True
        break

    time.sleep(2.0)

if activated:
    log.info("joint_group_controller activated successfully")
else:
    log.error("Failed to activate joint_group_controller after 30 attempts")

rclpy.shutdown()

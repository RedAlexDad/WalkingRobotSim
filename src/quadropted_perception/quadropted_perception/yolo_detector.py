#!/usr/bin/env python3
import os
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from cv_bridge import CvBridge
from ultralytics import YOLO
from quadropted_msgs.msg import Detection, DetectionArray


class YOLODetector(Node):
    def __init__(self):
        super().__init__("yolo_detector")

        self._bridge = CvBridge()
        self._model = None
        self._model_path = None

        self.declare_parameter("model_name", "yolov8n.pt")
        self.declare_parameter("model_path", "")
        self.declare_parameter("confidence_threshold", 0.5)
        self.declare_parameter("iou_threshold", 0.45)
        self.declare_parameter("camera_topic", "/robot1/color/image_raw")
        self.declare_parameter("target_classes", [])
        self.declare_parameter("device", "cpu")
        self.declare_parameter("frame_id", "camera_link")

        model_name = self.get_parameter("model_name").value
        model_path = self.get_parameter("model_path").value
        self._conf = self.get_parameter("confidence_threshold").value
        self._iou = self.get_parameter("iou_threshold").value
        camera_topic = self.get_parameter("camera_topic").value
        self._target_classes = self.get_parameter("target_classes").value
        device = self.get_parameter("device").value
        self._frame_id = self.get_parameter("frame_id").value

        resolved_path = self._resolve_model(model_path, model_name)
        self.get_logger().info(f"Loading YOLO model: {resolved_path} (device: {device})")
        self._model = YOLO(resolved_path)
        self._model.to(device)

        self._pub_detections = self.create_publisher(DetectionArray, "detections", 10)
        self._pub_debug_image = self.create_publisher(Image, "detected_image", 10)

        self._sub_camera = self.create_subscription(
            Image, camera_topic, self._image_callback, 10
        )

        self.get_logger().info(
            f"YOLO detector ready — model: {resolved_path}, topic: {camera_topic}, "
            f"conf: {self._conf}, iou: {self._iou}"
        )

    def _resolve_model(self, model_path, model_name):
        if model_path:
            path = os.path.expanduser(model_path)
            if os.path.isfile(path):
                self._model_path = path
                return path
            self.get_logger().warn(f"model_path not found: {path}, falling back to model_name")

        models_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "models"
        )
        local_path = os.path.join(models_dir, model_name)
        if os.path.isfile(local_path):
            self._model_path = local_path
            return local_path

        self._model_path = model_name
        return model_name

    def _image_callback(self, msg):
        try:
            cv_image = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"cv_bridge error: {e}")
            return

        results = self._model(
            cv_image,
            conf=self._conf,
            iou=self._iou,
            classes=self._target_classes if self._target_classes else None,
            verbose=False,
        )[0]

        detections_msg = DetectionArray()
        detections_msg.header = msg.header
        detections_msg.header.frame_id = self._frame_id

        if results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(float, box.xyxy[0])

                d = Detection()
                d.class_id = cls_id
                d.class_name = results.names[cls_id]
                d.confidence = conf
                d.center_x = (x1 + x2) / 2.0
                d.center_y = (y1 + y2) / 2.0
                d.width = x2 - x1
                d.height = y2 - y1
                detections_msg.detections.append(d)

        self._pub_detections.publish(detections_msg)

        annotated = results.plot()
        try:
            debug_msg = self._bridge.cv2_to_imgmsg(annotated, encoding="bgr8")
            debug_msg.header = msg.header
            self._pub_debug_image.publish(debug_msg)
        except Exception as e:
            self.get_logger().error(f"Failed to publish debug image: {e}")

    @property
    def model_path(self):
        return self._model_path


def main(args=None):
    rclpy.init(args=args)
    node = YOLODetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

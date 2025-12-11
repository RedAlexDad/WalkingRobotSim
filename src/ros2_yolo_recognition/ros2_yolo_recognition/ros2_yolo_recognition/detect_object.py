import os
import torch
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import numpy as np
from ament_index_python.packages import get_package_share_directory
from yolo_msgs.msg import (
    Detection,
    DetectionArray,
    BoundingBox2D,
    Pose2D,
    Point2D,
    Vector2,
)


class YoloDetectObjectTrain(Node):
    def __init__(self):
        super().__init__("detect_object")
        self.declare_parameter("model_path", "ascol_object_detect_0.2.pt")
        param_model_path = (
            self.get_parameter("model_path").get_parameter_value().string_value
        )
        package_share = get_package_share_directory("ros2_yolo_recognition")
        self.model_path = os.path.join(package_share, "models", param_model_path)

        try:
            # Выбор устройства (GPU или CPU)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.get_logger().info(f"Using device: {device}")

            # Загрузка модели на выбранное устройство
            self.model = YOLO(self.model_path).to(device)
            self.model.conf = 0.3  # Порог уверенности
            self.get_logger().info("YOLO model loaded successfully")
            self.get_logger().info(f"Model loaded from: {self.model_path}")
        except Exception as e:
            self.get_logger().error(f"Failed to load YOLO model: {str(e)}")
            raise
        self.bridge = CvBridge()
        self.frame_count = 0
        # Подписка на изображения
        self.image_sub = self.create_subscription(
            Image, "/rgb_cam/image_raw", self.image_callback, 10
        )
        # Публикация результатов
        self.detection_pub = self.create_publisher(DetectionArray, "/detections", 10)
        self.debug_pub = self.create_publisher(Image, "/yolo/debug_image", 10)
        self.top_class_pub = self.create_publisher(String, "/top_detection_class", 10)
        self.get_logger().info("YOLO Processor initialized")

    def image_callback(self, msg):
        self.frame_count += 5
        if self.frame_count % 5 != 0:  # Обрабатывать каждый пятый кадр
            return
        try:
            # self.get_logger().info('Received image')
            # Конвертация ROS Image в OpenCV
            try:
                cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
                # self.get_logger().info('Converted image to OpenCV')

                # Преобразование изображения в тензор и перемещение на GPU
                device = "cuda" if torch.cuda.is_available() else "cpu"
                tensor_image = torch.from_numpy(cv_image).to(device)

                # Перевод из BHWC в BCHW и нормализация значений пикселей
                tensor_image = (
                    tensor_image.permute(2, 0, 1).unsqueeze(0).float() / 255.0
                )
            except Exception as e:
                self.get_logger().error(f"CvBridge error: {str(e)}")
                return
            # Выполнение предсказания
            try:
                results = self.model(
                    tensor_image, verbose=False
                )  # verbose=False - отключение вывода на экран
                # self.get_logger().info(f'Got {len(results)} YOLO results')
            except Exception as e:
                self.get_logger().error(f"YOLO prediction error: {str(e)}")
                return
            # Подготовка сообщения DetectionArray
            detection_array = DetectionArray()
            detection_array.header = msg.header
            top_confidence = 0.0
            top_class = ""
            try:
                for r in results:
                    for box in r.boxes:
                        try:
                            class_id = int(box.cls.cpu().item())
                            score = float(box.conf.cpu().item())
                            bbox = box.xyxy.cpu().numpy()[0]
                            class_name = r.names[class_id]
                            # self.get_logger().info(f"Detected {class_name} with score {score}")

                            # Заполнение сообщения Detection
                            detection = Detection()
                            detection.class_id = class_id
                            detection.class_name = class_name
                            detection.score = score
                            # Заполнение BoundingBox2D
                            detection.bbox = BoundingBox2D()
                            detection.bbox.center = Pose2D()
                            detection.bbox.center.position = Point2D()
                            detection.bbox.center.position.x = (
                                bbox[0] + bbox[2]
                            ) / 2.0  # Центр x
                            detection.bbox.center.position.y = (
                                bbox[1] + bbox[3]
                            ) / 2.0  # Центр y
                            detection.bbox.center.theta = 0.0  # Без поворота
                            detection.bbox.size = Vector2()
                            detection.bbox.size.x = float(bbox[2] - bbox[0])  # Ширина
                            detection.bbox.size.y = float(bbox[3] - bbox[1])  # Высота
                            detection_array.detections.append(detection)

                            # Обновление топового класса
                            if score > top_confidence:
                                top_confidence = score
                                top_class = class_name
                        except Exception as e:
                            self.get_logger().error(f"Error processing box: {str(e)}")
                            continue
                # self.get_logger().info(f'Processed {len(detection_array.detections)} detections')
            except Exception as e:
                self.get_logger().error(f"Error processing detections: {str(e)}")
            # Публикация детекций
            try:
                self.detection_pub.publish(detection_array)
                # self.get_logger().info(f'Published {len(detection_array.detections)} detections')
                pass
            except Exception as e:
                self.get_logger().error(f"Error publishing detections: {str(e)}")
            # Публикация топового класса
            try:
                top_class_msg = String()
                top_class_msg.data = top_class
                self.top_class_pub.publish(top_class_msg)
                # self.get_logger().info(f'Published top class: {top_class}')
            except Exception as e:
                self.get_logger().error(f"Error publishing top class: {str(e)}")
            # Отрисовка и публикация отладочного изображения
            try:
                debug_image = results[0].plot()
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, encoding="bgr8")
                self.debug_pub.publish(debug_msg)
                # self.get_logger().info('Published debug image')
            except Exception as e:
                self.get_logger().error(f"Error publishing debug image: {str(e)}")
        except Exception as e:
            self.get_logger().error(f"General error in image_callback: {str(e)}")


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectObjectTrain()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

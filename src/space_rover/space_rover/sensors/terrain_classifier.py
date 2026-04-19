import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np


class TerrainClassifier(Node):
    def __init__(self):
        super().__init__('terrain_classifier')
        self.bridge = CvBridge()
        self.current_label = 'UNKNOWN'
        self.last_confidence = 0.0

        self.sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            qos_profile_sensor_data,
        )
        self.pub = self.create_publisher(String, '/terrain_type', 10)
        self.timer = self.create_timer(0.5, self.publish_current_label)

        self.get_logger().info('Terrain classifier started on /camera/image_raw')

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.current_label, self.last_confidence = self.classify(frame)
        except Exception as exc:
            self.get_logger().error(f'Terrain classification failed: {exc}')

    def classify(self, frame):
        height, width = frame.shape[:2]
        roi = frame[height // 5 : height - height // 10, width // 5 : width - width // 5]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        red_brown_mask = cv2.inRange(hsv, (5, 40, 30), (35, 255, 255))
        dark_mask = cv2.inRange(hsv, (0, 0, 0), (180, 255, 65))

        red_brown_ratio = float(np.count_nonzero(red_brown_mask)) / float(red_brown_mask.size)
        dark_ratio = float(np.count_nonzero(dark_mask)) / float(dark_mask.size)
        saturation = float(np.mean(hsv[:, :, 1]))
        value = float(np.mean(hsv[:, :, 2]))

        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max(20, min(roi.shape[:2]) // 4),
            param1=100,
            param2=25,
            minRadius=max(10, min(roi.shape[:2]) // 10),
            maxRadius=max(20, min(roi.shape[:2]) // 2),
        )

        if circles is not None and dark_ratio > 0.12:
            return 'CRATER', 0.92
        if red_brown_ratio > 0.18 or (saturation > 70 and value < 180):
            return 'ROCKY', min(0.95, 0.5 + red_brown_ratio)
        if value > 115 and saturation < 65 and dark_ratio < 0.1:
            return 'FLAT', 0.84
        return 'UNKNOWN', 0.35

    def publish_current_label(self):
        self.pub.publish(String(data=self.current_label))


def main(args=None):
    rclpy.init(args=args)
    node = TerrainClassifier()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
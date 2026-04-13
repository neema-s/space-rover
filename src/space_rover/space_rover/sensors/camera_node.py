import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')
        self.message_count = 0

        self.bridge = CvBridge()

        self.sub = self.create_subscription(
            Image,
            '/camera/camera_sensor/image_raw',
            self.callback,
            10
        )

        self.pub = self.create_publisher(Image, '/camera/image_raw', 10)

        self.get_logger().info("Camera Node Started (publishing /camera/image_raw)")

    def callback(self, msg):
        try:
            self.message_count += 1
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            cv2.putText(
                cv_image,
                "ROVER CAMERA",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            new_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding='bgr8')
            self.pub.publish(new_msg)

            if self.message_count == 1 or self.message_count % 30 == 0:
                self.get_logger().info(
                    f'Camera update #{self.message_count}: {msg.width}x{msg.height}'
                )

        except Exception as e:
            self.get_logger().error(f"Camera error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
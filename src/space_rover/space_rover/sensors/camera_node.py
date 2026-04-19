import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')
        self.message_count = 0

        self.sub = self.create_subscription(
            Image,
            '/camera/camera_sensor/image_raw',
            self.callback,
            qos_profile_sensor_data
        )

        self.pub = self.create_publisher(Image, '/camera/image_raw', qos_profile_sensor_data)

        self.get_logger().info("Camera Node Started (publishing /camera/image_raw)")

    def callback(self, msg):
        try:
            self.message_count += 1
            # Forward the camera frame as-is to keep the dashboard feed reliable.
            self.pub.publish(msg)

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
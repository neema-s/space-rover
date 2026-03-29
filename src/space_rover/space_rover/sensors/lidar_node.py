import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class LidarNode(Node):
    def __init__(self):
        super().__init__('lidar_node')

        # Subscribe to the Gazebo LIDAR topic and republish processed data
        self.sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.callback,
            10
        )
        # Fallback subscription to the plugin's raw output topic
        self.sub_raw = self.create_subscription(
            LaserScan,
            '/gazebo_ros_lidar/out',
            self.callback,
            10
        )

        self.pub = self.create_publisher(LaserScan, '/scan/processed', 10)

        self.get_logger().info('LIDAR Node Started (listening on /scan and /gazebo_ros_lidar/out)')

    def callback(self, msg: LaserScan):
        try:
            # Placeholder for processing. Currently forwards the raw scan.
            self.pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Lidar processing error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = LidarNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math
import random

class LidarNode(Node):
    def __init__(self):
        super().__init__('lidar_node')

        self.pub = self.create_publisher(LaserScan, '/scan', 10)
        self.timer = self.create_timer(0.1, self.publish_scan)

        self.get_logger().info("LIDAR Node Started")

    def publish_scan(self):
        msg = LaserScan()

        msg.header.frame_id = "laser_frame"
        msg.header.stamp = self.get_clock().now().to_msg()

        msg.angle_min = -1.57
        msg.angle_max = 1.57
        msg.angle_increment = 0.01

        msg.range_min = 0.1
        msg.range_max = 10.0

        num_readings = int((msg.angle_max - msg.angle_min) / msg.angle_increment)

        msg.ranges = [
            random.uniform(0.5, 5.0) for _ in range(num_readings)
        ]

        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = LidarNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist
import numpy as np

class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.obs_pub = self.create_publisher(Bool, '/obstacle_detected', 10)

    def scan_callback(self, msg):
        ranges = np.array(msg.ranges)

        # front arc
        front = ranges[len(ranges)//3 : 2*len(ranges)//3]

        if np.any(front < 0.8):
            self.get_logger().info("Obstacle detected!")

            self.obs_pub.publish(Bool(data=True))

            twist = Twist()
            twist.angular.z = 0.5
            self.cmd_pub.publish(twist)
        else:
            self.obs_pub.publish(Bool(data=False))


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

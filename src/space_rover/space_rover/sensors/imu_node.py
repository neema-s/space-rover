import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import random

class ImuNode(Node):
    def __init__(self):
        super().__init__('imu_node')

        self.pub = self.create_publisher(Imu, '/imu/data', 10)
        self.timer = self.create_timer(0.1, self.publish_imu)

        self.get_logger().info("IMU Node Started")

    def publish_imu(self):
        msg = Imu()

        msg.header.frame_id = "imu_link"
        msg.header.stamp = self.get_clock().now().to_msg()

        # Fake orientation
        msg.orientation.w = 1.0

        # Fake angular velocity
        msg.angular_velocity.x = random.uniform(-0.1, 0.1)
        msg.angular_velocity.y = random.uniform(-0.1, 0.1)
        msg.angular_velocity.z = random.uniform(-0.1, 0.1)

        # Fake linear acceleration
        msg.linear_acceleration.x = random.uniform(-0.5, 0.5)
        msg.linear_acceleration.y = random.uniform(-0.5, 0.5)
        msg.linear_acceleration.z = random.uniform(-0.5, 0.5)

        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
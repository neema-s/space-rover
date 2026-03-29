import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class ImuNode(Node):
    def __init__(self):
        super().__init__('imu_node')

        # Subscribe to IMU data published by Gazebo plugin
        self.sub = self.create_subscription(
            Imu,
            '/imu/data',
            self.callback,
            10
        )
        # Also subscribe to the plugin's raw topic in case remapping isn't applied
        self.sub_raw = self.create_subscription(
            Imu,
            '/imu/gazebo_ros_imu/out',
            self.callback,
            10
        )

        # Optional processed IMU topic
        self.pub = self.create_publisher(Imu, '/imu/processed', 10)

        self.get_logger().info("IMU Node Started (listening on /imu/data and /imu/gazebo_ros_imu/out)")

    def callback(self, msg: Imu):
        # For now, simply forward received IMU messages to /imu/processed
        try:
            self.pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Failed to republish IMU message: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
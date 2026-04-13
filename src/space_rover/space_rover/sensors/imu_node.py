import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class ImuNode(Node):
    def __init__(self):
        super().__init__('imu_node')
        self.message_count = 0

        # Subscribe to IMU data published by Gazebo plugin
        self.sub = self.create_subscription(
            Imu,
            '/imu/gazebo_ros_imu/out',
            self.callback,
            10
        )

        self.pub = self.create_publisher(Imu, '/imu/data', 10)

        self.get_logger().info("IMU Node Started (listening on /imu/gazebo_ros_imu/out, publishing /imu/data)")

    def callback(self, msg: Imu):
        try:
            self.message_count += 1
            if self.message_count == 1 or self.message_count % 20 == 0:
                self.get_logger().info(
                    f'IMU update #{self.message_count}: '
                    f'orientation=({msg.orientation.x:.2f}, {msg.orientation.y:.2f}, {msg.orientation.z:.2f}, {msg.orientation.w:.2f})'
                )
            self.pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Failed to republish IMU message: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
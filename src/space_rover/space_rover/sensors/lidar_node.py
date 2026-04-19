import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class LidarNode(Node):
    def __init__(self):
        super().__init__('lidar_node')
        self.message_count = 0

        # Subscribe to the Gazebo LIDAR topic and republish the demo LaserScan topic.
        self.sub = self.create_subscription(
            LaserScan,
            '/gazebo_ros_lidar/out',
            self.callback,
            qos_profile_sensor_data
        )

        self.pub = self.create_publisher(LaserScan, '/scan', qos_profile_sensor_data)

        self.get_logger().info('LIDAR Node Started (listening on /gazebo_ros_lidar/out, publishing /scan)')

    def callback(self, msg: LaserScan):
        try:
            self.message_count += 1
            if self.message_count == 1 or self.message_count % 20 == 0:
                range_count = len(msg.ranges)
                first_range = msg.ranges[0] if range_count > 0 else float('nan')
                self.get_logger().info(
                    f'LIDAR update #{self.message_count}: ranges={range_count}, first_range={first_range:.2f}'
                )
            self.pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Lidar processing error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = LidarNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
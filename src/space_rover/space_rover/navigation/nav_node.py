import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

class NavNode(Node):
    def __init__(self):
        super().__init__('nav_node')

        self.goal_sub = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_callback,
            10
        )

        self.get_logger().info("Navigation Node Started")

    def goal_callback(self, msg):
        self.get_logger().info(
            f"Received goal: x={msg.pose.position.x}, y={msg.pose.position.y}"
        )

def main(args=None):
    rclpy.init(args=args)
    node = NavNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

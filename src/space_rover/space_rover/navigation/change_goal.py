import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

class GoalPublisher(Node):
    def __init__(self):
        super().__init__('goal_publisher')
        self.pub = self.create_publisher(PoseStamped, '/goal_pose', 10)

        msg = PoseStamped()
        msg.header.frame_id = 'map'

        msg.pose.position.x = 2.0
        msg.pose.position.y = 2.0

        self.pub.publish(msg)
        self.get_logger().info("Goal sent!")


def main():
    rclpy.init()
    node = GoalPublisher()
    rclpy.spin_once(node)
    node.destroy_node()
    rclpy.shutdown()

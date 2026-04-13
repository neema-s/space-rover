import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
import math

class NavNode(Node):
    def __init__(self):
        super().__init__('nav_node')

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.goal_sub = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_callback,
            10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.goal = None
        self.current_pose = None

        self.timer = self.create_timer(0.1, self.navigate)

        self.get_logger().info("Navigation Node Started")

    def goal_callback(self, msg):
        self.goal = msg.pose
        self.get_logger().info("New goal received!")

    def odom_callback(self, msg):
        self.current_pose = msg.pose.pose

    def navigate(self):
        if self.goal is None or self.current_pose is None:
            return

        dx = self.goal.position.x - self.current_pose.position.x
        dy = self.goal.position.y - self.current_pose.position.y

        distance = math.sqrt(dx*dx + dy*dy)

        if distance < 0.3:
            self.get_logger().info("Goal reached!")
            self.cmd_pub.publish(Twist())
            self.goal = None
            return

        angle_to_goal = math.atan2(dy, dx)

        twist = Twist()
        twist.linear.x = 0.5
        twist.angular.z = angle_to_goal * 0.5

        self.cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = NavNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

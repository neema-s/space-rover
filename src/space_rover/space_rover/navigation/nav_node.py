import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool
import math


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class NavNode(Node):
    def __init__(self):
        super().__init__('nav_node')

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.teleop_sub = self.create_subscription(
            Twist,
            '/cmd_vel_teleop',
            self.teleop_callback,
            10
        )

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

        self.obstacle_sub = self.create_subscription(
            Bool,
            '/obstacle_detected',
            self.obstacle_callback,
            10
        )

        self.goal = None
        self.current_pose = None
        self.obstacle_detected = False
        self.teleop_cmd = None
        self.last_teleop_time = 0

        self.timer = self.create_timer(0.1, self.navigate)

        self.get_logger().info("Navigation Node Started")

    def teleop_callback(self, msg):
        self.teleop_cmd = msg
        self.last_teleop_time = self.get_clock().now().nanoseconds

    def goal_callback(self, msg):
        self.goal = msg.pose
        self.get_logger().info("New goal received!")

    def odom_callback(self, msg):
        self.current_pose = msg.pose.pose

    def obstacle_callback(self, msg):
        self.obstacle_detected = msg.data

    def navigate(self):
        if self.obstacle_detected:
            # Let obstacle handler own /cmd_vel while hazard is active.
            return

        now_ns = self.get_clock().now().nanoseconds
        if self.teleop_cmd is not None and (now_ns - self.last_teleop_time) < 500_000_000:
            self.cmd_pub.publish(self.teleop_cmd)
            return

        if self.goal is None or self.current_pose is None:
            return

        dx = self.goal.position.x - self.current_pose.position.x
        dy = self.goal.position.y - self.current_pose.position.y

        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.3:
            self.get_logger().info("Goal reached!")
            self.cmd_pub.publish(Twist())
            self.goal = None
            return

        angle_to_goal = math.atan2(dy, dx)
        current_yaw = yaw_from_quaternion(self.current_pose.orientation)
        heading_error = normalize_angle(angle_to_goal - current_yaw)

        twist = Twist()
        twist.angular.z = max(-0.8, min(0.8, 1.2 * heading_error))

        # Slow down while turning hard so rover does not skid into terrain edges.
        if abs(heading_error) > 0.6:
            twist.linear.x = 0.12
        else:
            twist.linear.x = min(0.45, 0.2 + 0.15 * distance)

        self.cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = NavNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

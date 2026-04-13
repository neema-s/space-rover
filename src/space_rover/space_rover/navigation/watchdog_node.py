import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import time
import math


class Watchdog(Node):
    def __init__(self):
        super().__init__('watchdog')

        # Subscribers
        self.cmd_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_callback,
            10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        # Publishers
        self.status_pub = self.create_publisher(String, '/rover_status', 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # State variables
        self.current_position = None
        self.last_position = None
        self.last_move_time = time.time()

        self.recovery_attempts = 0
        self.max_recovery_attempts = 3

        # Timer
        self.timer = self.create_timer(1.0, self.check_status)

        self.get_logger().info("Watchdog Node Started")

    # ---------------------------
    # Callbacks
    # ---------------------------
    def cmd_callback(self, msg):
        # If robot is commanded to move, update time
        if abs(msg.linear.x) > 0.01 or abs(msg.angular.z) > 0.01:
            self.last_move_time = time.time()

    def odom_callback(self, msg):
        self.current_position = msg.pose.pose.position

    # ---------------------------
    # Main Watchdog Logic
    # ---------------------------
    def check_status(self):
        if self.current_position is None:
            return

        if self.last_position is None:
            self.last_position = self.current_position
            return

        dx = self.current_position.x - self.last_position.x
        dy = self.current_position.y - self.last_position.y

        distance = math.sqrt(dx * dx + dy * dy)

        # ---------------------------
        # STUCK DETECTION
        # ---------------------------
        if distance < 0.01:
            if time.time() - self.last_move_time > 3.0:

                if self.recovery_attempts < self.max_recovery_attempts:
                    self.get_logger().warn(
                        f"Robot STUCK! Attempting recovery ({self.recovery_attempts + 1})"
                    )

                    self.status_pub.publish(String(data="ERROR"))

                    self.recover()

                    self.recovery_attempts += 1
                    self.last_move_time = time.time()

                else:
                    self.get_logger().error("Robot permanently STUCK!")
                    self.status_pub.publish(String(data="STUCK"))

        else:
            # Robot is moving normally
            self.recovery_attempts = 0
            self.status_pub.publish(String(data="MOVING"))

        self.last_position = self.current_position

    # ---------------------------
    # Recovery Behavior
    # ---------------------------
    def recover(self):
        twist = Twist()
        twist.angular.z = 0.5  # rotate in place

        # Rotate for short duration
        for _ in range(10):
            self.cmd_pub.publish(twist)
            time.sleep(0.1)

        # Stop after recovery
        self.cmd_pub.publish(Twist())


# ---------------------------
# Main
# ---------------------------
def main(args=None):
    rclpy.init(args=args)
    node = Watchdog()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

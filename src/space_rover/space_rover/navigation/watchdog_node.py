import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
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
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # State variables
        self.current_position = None
        self.last_position = None
        self.last_move_time = time.time()
        self.command_active = False

        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        self.recovery_mode = False
        self.recovery_phase = 'IDLE'
        self.recovery_end_time = 0.0

        # Timer
        self.timer = self.create_timer(0.1, self.check_status)

        self.get_logger().info("Watchdog Node Started")

    # ---------------------------
    # Callbacks
    # ---------------------------
    def cmd_callback(self, msg):
        # If robot is commanded to move, update time
        if abs(msg.linear.x) > 0.01 or abs(msg.angular.z) > 0.01:
            self.command_active = True
            self.last_move_time = time.time()
        else:
            self.command_active = False

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

        if self.recovery_mode:
            self.run_recovery()
            self.last_position = self.current_position
            return

        if not self.command_active:
            self.recovery_attempts = 0
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

                    self.recover()

                    self.recovery_attempts += 1
                    self.last_move_time = time.time()

                else:
                    self.get_logger().error("Robot permanently STUCK!")

        else:
            # Robot is moving normally
            self.recovery_attempts = 0

        self.last_position = self.current_position

    # ---------------------------
    # Recovery Behavior
    # ---------------------------
    def recover(self):
        self.recovery_mode = True
        self.recovery_phase = 'TURN'
        self.recovery_end_time = time.time() + 1.0

    def run_recovery(self):
        now = time.time()
        twist = Twist()

        if self.recovery_phase == 'TURN':
            twist.angular.z = 0.5
            self.cmd_pub.publish(twist)
            if now >= self.recovery_end_time:
                self.recovery_phase = 'FORWARD'
                self.recovery_end_time = now + 0.8
            return

        if self.recovery_phase == 'FORWARD':
            twist.linear.x = 0.15
            self.cmd_pub.publish(twist)
            if now >= self.recovery_end_time:
                self.cmd_pub.publish(Twist())
                self.recovery_mode = False
                self.recovery_phase = 'IDLE'
                self.recovery_end_time = 0.0


# ---------------------------
# Main
# ---------------------------
def main(args=None):
    rclpy.init(args=args)
    node = Watchdog()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

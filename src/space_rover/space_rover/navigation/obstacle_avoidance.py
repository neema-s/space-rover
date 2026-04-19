import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String
from geometry_msgs.msg import Twist
import numpy as np


class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data
        )

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.obs_pub = self.create_publisher(Bool, '/obstacle_detected', 10)

        self.terrain_sub = self.create_subscription(
            String,
            '/terrain_type',
            self.terrain_callback,
            10
        )

        self.latest_scan = None
        self.current_terrain = 'UNKNOWN'
        self.avoidance_mode = 'CLEAR'
        self.step_deadline_ns = 0
        self.create_timer(0.1, self.control_loop)

    def scan_callback(self, msg):
        self.latest_scan = msg

    def terrain_callback(self, msg):
        self.current_terrain = msg.data

    def _front_is_blocked(self):
        if self.latest_scan is None or len(self.latest_scan.ranges) == 0:
            return False

        ranges = np.array(self.latest_scan.ranges, dtype=np.float32)
        finite = np.isfinite(ranges)
        ranges = ranges[finite]
        if ranges.size == 0:
            return False

        # Use 60-degree front cone centered around heading.
        full = np.array(self.latest_scan.ranges, dtype=np.float32)
        mid = len(full) // 2
        span = max(1, len(full) // 12)
        front = full[mid - span : mid + span + 1]
        front = front[np.isfinite(front)]
        if front.size == 0:
            return False

        return float(np.min(front)) < 0.8

    def control_loop(self):
        now_ns = self.get_clock().now().nanoseconds

        crater_detected = self.current_terrain == 'CRATER'
        obstacle_detected = self._front_is_blocked()
        hazard = crater_detected or obstacle_detected

        if self.avoidance_mode == 'CLEAR' and hazard:
            # Crater policy: do not enter crater. Stop, reverse, then rotate away.
            self.avoidance_mode = 'REVERSE'
            self.step_deadline_ns = now_ns + int(1.4e9)
            self.get_logger().warn('Hazard detected (obstacle/crater). Starting avoidance.')

        if self.avoidance_mode != 'CLEAR':
            self.obs_pub.publish(Bool(data=True))
            twist = Twist()

            if self.avoidance_mode == 'REVERSE':
                twist.linear.x = -0.2
                twist.angular.z = 0.0
                if now_ns >= self.step_deadline_ns:
                    self.avoidance_mode = 'TURN'
                    self.step_deadline_ns = now_ns + int(1.8e9)

            elif self.avoidance_mode == 'TURN':
                twist.linear.x = 0.0
                twist.angular.z = 0.65
                if now_ns >= self.step_deadline_ns and not hazard:
                    self.avoidance_mode = 'CLEAR'

            self.cmd_pub.publish(twist)
            return

        self.obs_pub.publish(Bool(data=False))


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

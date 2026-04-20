import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String
from geometry_msgs.msg import Twist
import numpy as np
import math


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
        self.turn_direction = 1.0
        self.step_deadline_ns = 0
        self.create_timer(0.1, self.control_loop)

    def scan_callback(self, msg):
        self.latest_scan = msg

    def terrain_callback(self, msg):
        self.current_terrain = msg.data

    def _sector_min(self, center_deg, half_width_deg):
        if self.latest_scan is None or len(self.latest_scan.ranges) == 0:
            return float('inf')

        mins = []
        center = math.radians(center_deg)
        half_width = math.radians(half_width_deg)
        angle = self.latest_scan.angle_min

        for distance in self.latest_scan.ranges:
            if abs(self._normalize_angle(angle - center)) <= half_width and math.isfinite(distance):
                mins.append(distance)
            angle += self.latest_scan.angle_increment

        if not mins:
            return float('inf')
        return float(min(mins))

    def _normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    def _front_is_blocked(self):
        return self._sector_min(0.0, 24.0) < 1.15

    def _pick_turn_direction(self):
        left_clearance = self._sector_min(55.0, 30.0)
        right_clearance = self._sector_min(-55.0, 30.0)
        return 1.0 if left_clearance >= right_clearance else -1.0

    def control_loop(self):
        now_ns = self.get_clock().now().nanoseconds

        crater_detected = self.current_terrain == 'CRATER'
        obstacle_detected = self._front_is_blocked()
        hazard = crater_detected or obstacle_detected

        if self.avoidance_mode == 'CLEAR' and hazard:
            # Bug-style reactive avoidance: stop, turn toward the freer side,
            # then follow the obstacle boundary with a shallow forward arc
            # until the front sector clears again.
            self.turn_direction = self._pick_turn_direction()
            self.avoidance_mode = 'REVERSE'
            self.step_deadline_ns = now_ns + int(0.9e9)
            self.get_logger().warn(
                f'Hazard detected (obstacle/crater). Starting Bug-style avoidance, '
                f'turning {"left" if self.turn_direction > 0 else "right"}.'
            )

        if self.avoidance_mode != 'CLEAR':
            self.obs_pub.publish(Bool(data=True))
            twist = Twist()

            if self.avoidance_mode == 'REVERSE':
                twist.linear.x = -0.18
                twist.angular.z = 0.0
                if now_ns >= self.step_deadline_ns:
                    self.avoidance_mode = 'TURN'
                    self.step_deadline_ns = now_ns + int(1.8e9)

            elif self.avoidance_mode == 'TURN':
                twist.linear.x = 0.0
                twist.angular.z = 0.75 * self.turn_direction
                side_sector = 70.0 if self.turn_direction > 0 else -70.0
                side_clear = self._sector_min(side_sector, 24.0) > 0.95
                front_clear = self._sector_min(0.0, 20.0) > 1.35
                if now_ns >= self.step_deadline_ns and (front_clear or side_clear):
                    self.avoidance_mode = 'FOLLOW_EDGE'
                    self.step_deadline_ns = now_ns + int(2.4e9)

            elif self.avoidance_mode == 'FOLLOW_EDGE':
                twist.linear.x = 0.18
                twist.angular.z = -0.28 * self.turn_direction

                front_clear = self._sector_min(0.0, 18.0) > 1.45
                flank_too_close = self._sector_min(
                    80.0 if self.turn_direction > 0 else -80.0,
                    18.0,
                ) < 0.55
                if flank_too_close:
                    twist.angular.z = 0.18 * self.turn_direction

                if now_ns >= self.step_deadline_ns and front_clear:
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

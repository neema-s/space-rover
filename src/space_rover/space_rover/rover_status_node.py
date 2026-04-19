import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool, String


class RoverStatusNode(Node):
    def __init__(self):
        super().__init__('rover_status')

        self.estop_active = False
        self.obstacle_detected = False
        self.last_cmd = Twist()
        self.last_cmd_time = self.get_clock().now()
        self.last_motion_time = self.get_clock().now()
        self.last_error_time = None
        self.last_pose = None
        self.current_pose = None
        self.current_state = 'STOPPED'

        self.create_subscription(Bool, '/emergency_stop', self.estop_callback, 10)
        self.create_subscription(Bool, '/obstacle_detected', self.obstacle_callback, 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        self.status_pub = self.create_publisher(String, '/rover_status', 10)
        self.create_timer(0.2, self.publish_status)

        self.get_logger().info('Rover status node started')

    def estop_callback(self, msg):
        self.estop_active = msg.data

    def obstacle_callback(self, msg):
        self.obstacle_detected = msg.data

    def cmd_callback(self, msg):
        self.last_cmd = msg
        self.last_cmd_time = self.get_clock().now()

    def odom_callback(self, msg):
        self.current_pose = msg.pose.pose.position
        if self.last_pose is None:
            self.last_pose = self.current_pose
            return

        distance = math.hypot(
            self.current_pose.x - self.last_pose.x,
            self.current_pose.y - self.last_pose.y,
        )
        if distance > 0.01:
            self.last_motion_time = self.get_clock().now()
        self.last_pose = self.current_pose

    def publish_status(self):
        now = self.get_clock().now()
        command_active = abs(self.last_cmd.linear.x) > 0.01 or abs(self.last_cmd.angular.z) > 0.01
        moving_recently = (now - self.last_motion_time).nanoseconds < 2_000_000_000
        command_recent = (now - self.last_cmd_time).nanoseconds < 3_000_000_000

        if self.estop_active:
            state = 'ESTOP'
        elif self.obstacle_detected:
            state = 'OBSTACLE_DETECTED'
        elif command_active and moving_recently:
            state = 'MOVING'
        elif command_active and command_recent and not moving_recently:
            state = 'RECOVERY'
        elif command_active and not command_recent and not moving_recently:
            state = 'ERROR'
            self.last_error_time = now
        elif self.last_error_time is not None and (now - self.last_error_time).nanoseconds < 5_000_000_000:
            state = 'RECOVERY'
        else:
            state = 'STOPPED'

        self.current_state = state
        self.status_pub.publish(String(data=state))


def main(args=None):
    rclpy.init(args=args)
    node = RoverStatusNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

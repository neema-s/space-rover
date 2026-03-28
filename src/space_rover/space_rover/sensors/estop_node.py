import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist

class EStopNode(Node):
    def __init__(self):
        super().__init__('estop_node')

        self.estop_active = False

        self.sub = self.create_subscription(
            Bool,
            '/emergency_stop',
            self.callback,
            10
        )

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.timer = self.create_timer(0.1, self.enforce_stop)

        self.get_logger().info("E-STOP Node Started")

    def callback(self, msg):
        self.estop_active = msg.data

        if self.estop_active:
            self.get_logger().warn("EMERGENCY STOP ACTIVATED!")
            self.publish_zero()

        else:
            self.get_logger().info("E-STOP RELEASED")

    def publish_zero(self):
        twist = Twist()
        self.pub.publish(twist)

    def enforce_stop(self):
        if self.estop_active:
            self.publish_zero()

def main(args=None):
    rclpy.init(args=args)
    node = EStopNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
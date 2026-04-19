import csv
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool, String


class MissionLogger(Node):
    def __init__(self):
        super().__init__('mission_logger')

        self.package_root = Path(__file__).resolve().parents[1]
        self.log_dir = self.package_root / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / 'mission_log.csv'

        self.current_status = 'UNKNOWN'
        self.current_terrain = 'UNKNOWN'
        self.current_pose = None
        self.estop_active = False
        self.previous_pose = None
        self.total_distance = 0.0
        self.estop_events = 0
        self.last_estop_state = False

        self.create_subscription(String, '/rover_status', self.status_callback, 10)
        self.create_subscription(String, '/terrain_type', self.terrain_callback, 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.create_subscription(Bool, '/emergency_stop', self.estop_callback, 10)

        self.file = self.log_path.open('w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['timestamp', 'x_pos', 'y_pos', 'rover_status', 'terrain_type', 'estop_active'])
        self.file.flush()

        self.create_timer(2.0, self.write_row)
        self.get_logger().info(f'Mission logger writing to {self.log_path}')

    def status_callback(self, msg):
        self.current_status = msg.data

    def terrain_callback(self, msg):
        self.current_terrain = msg.data

    def odom_callback(self, msg):
        position = msg.pose.pose.position
        self.current_pose = position
        if self.previous_pose is not None:
            dx = position.x - self.previous_pose.x
            dy = position.y - self.previous_pose.y
            self.total_distance += (dx * dx + dy * dy) ** 0.5
        self.previous_pose = position

    def estop_callback(self, msg):
        self.estop_active = msg.data
        if self.estop_active and not self.last_estop_state:
            self.estop_events += 1
        self.last_estop_state = self.estop_active

    def write_row(self):
        timestamp = datetime.now().isoformat(timespec='seconds')
        x_pos = self.current_pose.x if self.current_pose is not None else 0.0
        y_pos = self.current_pose.y if self.current_pose is not None else 0.0
        self.writer.writerow([
            timestamp,
            f'{x_pos:.3f}',
            f'{y_pos:.3f}',
            self.current_status,
            self.current_terrain,
            str(self.estop_active),
        ])
        self.file.flush()

    def destroy_node(self):
        self.get_logger().info(
            f'Mission summary: distance={self.total_distance:.2f}m, estops={self.estop_events}, terrain={self.current_terrain}'
        )
        try:
            self.file.close()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MissionLogger()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

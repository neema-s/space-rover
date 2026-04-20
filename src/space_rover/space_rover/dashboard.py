import base64
import math
import os
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime

import cv2
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import Bool, String


@dataclass
class DashboardState:
    rover_status: str = 'STOPPED'
    terrain_type: str = 'UNKNOWN'
    estop_active: bool = False
    camera_frame: object = None
    scan: object = None
    goal_pose: object = None
    speed_mps: float = 0.0
    waypoint_index: int = 0
    waypoint_total: int = 3
    last_camera_time: float = 0.0
    last_scan_time: float = 0.0


@dataclass
class PanelRefs:
    frame: tk.Frame
    content: tk.Frame


class DashboardNode(Node):
    def __init__(self):
        super().__init__('dashboard')
        self.bridge = CvBridge()
        self.state = DashboardState()
        self.speed_scale = 0.4
        self.mission_start = time.monotonic()

        self.create_subscription(Image, '/camera/image_raw', self.camera_callback, qos_profile_sensor_data)
        self.create_subscription(LaserScan, '/scan', self.scan_callback, qos_profile_sensor_data)
        self.create_subscription(String, '/rover_status', self.status_callback, 10)
        self.create_subscription(String, '/terrain_type', self.terrain_callback, 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.create_subscription(PoseStamped, '/goal_pose', self.goal_callback, 10)
        self.create_subscription(Bool, '/emergency_stop', self.estop_callback, 10)

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.estop_pub = self.create_publisher(Bool, '/emergency_stop', 10)

    def camera_callback(self, msg):
        try:
            self.state.camera_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.state.last_camera_time = time.monotonic()
        except Exception as exc:
            self.get_logger().error(f'Camera decode failed: {exc}')

    def scan_callback(self, msg):
        self.state.scan = msg
        self.state.last_scan_time = time.monotonic()

    def status_callback(self, msg):
        self.state.rover_status = msg.data

    def terrain_callback(self, msg):
        self.state.terrain_type = msg.data

    def odom_callback(self, msg):
        linear = msg.twist.twist.linear
        self.state.speed_mps = math.sqrt(
            linear.x * linear.x + linear.y * linear.y + linear.z * linear.z
        )

    def goal_callback(self, msg):
        self.state.goal_pose = msg
        self.state.waypoint_index = min(self.state.waypoint_index + 1, self.state.waypoint_total)

    def estop_callback(self, msg):
        self.state.estop_active = msg.data

    def publish_twist(self, linear=0.0, angular=0.0):
        if not rclpy.ok():
            return
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        try:
            self.cmd_pub.publish(twist)
        except Exception:
            pass

    def publish_estop(self, active):
        if not rclpy.ok():
            return
        try:
            self.estop_pub.publish(Bool(data=active))
        except Exception:
            pass


class RoverDashboardApp:
    def __init__(self, node):
        self.node = node
        self.root = tk.Tk()
        self.root.title('Space Rover Dashboard')
        self.root.geometry('1280x780+30+30')
        self.root.configure(bg='#0b1016')
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.focus_force()
        self.root.after(100, self.root.lift)
        self.root.after(200, self.root.deiconify)
        self.root.after(300, self.root.focus_force)
        self.root.after(1200, lambda: self.root.attributes('-topmost', False))

        self.theme = {
            'bg': '#0b1016',
            'panel': '#121926',
            'panel_alt': '#182233',
            'text': '#e7edf7',
            'muted': '#95a4ba',
            'accent': '#f5a524',
            'good': '#2fd67b',
            'warn': '#ffb020',
            'bad': '#ff5c6c',
            'info': '#5aa9ff',
        }

        self.current_photo = None
        self.last_log_snapshot = {}
        self.event_history = ['Dashboard ready. Use the controls or SPACE for emergency stop.']
        self._build_ui()
        self._bind_keys()
        self.root.after(80, self.refresh_ui)

    def _panel(self, parent, title):
        frame = tk.Frame(parent, bg=self.theme['panel'], highlightbackground='#253246', highlightthickness=1)
        tk.Label(frame, text=title, fg=self.theme['text'], bg=self.theme['panel'], font=('TkDefaultFont', 13, 'bold')).pack(anchor='w', padx=12, pady=(10, 4))
        content = tk.Frame(frame, bg=self.theme['panel'])
        content.pack(fill='both', expand=True)
        return PanelRefs(frame=frame, content=content)

    def _status_row(self, parent, label):
        row = tk.Frame(parent, bg=self.theme['panel'])
        row.pack(fill='x', padx=12, pady=4)
        row.columnconfigure(1, weight=1)
        tk.Label(row, text=label, fg=self.theme['muted'], bg=self.theme['panel'], width=14, anchor='w').grid(row=0, column=0, sticky='w')
        value = tk.Label(row, text='--', fg=self.theme['text'], bg=self.theme['panel'], anchor='w')
        value.grid(row=0, column=1, sticky='w')
        return value

    def _button(self, parent, text, command, bg=None):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg or self.theme['accent'],
            fg='#0b1016',
            activebackground=self.theme['warn'],
            activeforeground='#0b1016',
            relief='flat',
            padx=12,
            pady=8,
            font=('TkDefaultFont', 10, 'bold'),
        )

    def _build_ui(self):
        header = tk.Frame(self.root, bg=self.theme['bg'])
        header.pack(fill='x', padx=18, pady=(16, 10))

        tk.Label(
            header,
            text='Space Rover Command Dashboard',
            fg=self.theme['text'],
            bg=self.theme['bg'],
            font=('TkDefaultFont', 22, 'bold'),
        ).pack(side='left')

        self.clock_label = tk.Label(header, fg=self.theme['muted'], bg=self.theme['bg'], font=('TkDefaultFont', 11))
        self.clock_label.pack(side='right')

        main = tk.Frame(self.root, bg=self.theme['bg'])
        main.pack(fill='both', expand=True, padx=16, pady=10)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        self.camera_panel = self._panel(main, 'Live Camera Feed')
        self.camera_panel.frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10), pady=(0, 10))
        self.camera_label = tk.Label(
            self.camera_panel.content,
            bg='#000000',
            fg=self.theme['text'],
            text='Waiting for /camera/image_raw...\nExpected: forward rover view from gazebo camera',
            justify='center',
        )
        self.camera_label.pack(fill='both', expand=True, padx=12, pady=12)

        self.scan_panel = self._panel(main, 'LIDAR Scan')
        self.scan_panel.frame.grid(row=0, column=1, sticky='nsew', pady=(0, 10))
        self.scan_canvas = tk.Canvas(self.scan_panel.content, bg='#09101a', highlightthickness=0)
        self.scan_canvas.pack(fill='both', expand=True, padx=12, pady=12)
        self.scan_hint = tk.Label(
            self.scan_panel.content,
            text='Expected: radial lines.\nLong lines = open space, short lines = nearby obstacle.',
            fg=self.theme['muted'],
            bg=self.theme['panel'],
            justify='left',
        )
        self.scan_hint.pack(anchor='w', padx=12, pady=(0, 8))

        controls = self._panel(main, 'Controls')
        controls.frame.grid(row=1, column=0, sticky='nsew', padx=(0, 10))

        state = self._panel(main, 'Mission State')
        state.frame.grid(row=1, column=1, sticky='nsew')
        state.content.columnconfigure(0, weight=1)

        status_frame = tk.Frame(controls.content, bg=self.theme['panel'])
        status_frame.pack(side='left', fill='both', expand=True, padx=12, pady=12)

        slider_frame = tk.Frame(controls.content, bg=self.theme['panel'])
        slider_frame.pack(side='right', fill='both', expand=True, padx=12, pady=12)

        self.status_value = self._status_row(status_frame, 'Rover status')
        self.terrain_value = self._status_row(status_frame, 'Terrain type')
        self.estop_value = self._status_row(status_frame, 'E-Stop')
        self.speed_value = self._status_row(status_frame, 'Speed')
        self.timer_value = self._status_row(status_frame, 'Mission timer')
        self.waypoint_value = self._status_row(status_frame, 'Waypoint')
        self.goal_value = self._status_row(status_frame, 'Goal pose')

        tk.Label(slider_frame, text='Speed control', fg=self.theme['text'], bg=self.theme['panel'], font=('TkDefaultFont', 12, 'bold')).pack(anchor='w')
        self.speed_slider = tk.Scale(
            slider_frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient='horizontal',
            length=260,
            bg=self.theme['panel'],
            fg=self.theme['text'],
            highlightthickness=0,
            troughcolor=self.theme['panel_alt'],
            command=self.on_speed_change,
        )
        self.speed_slider.set(0.4)
        self.speed_slider.pack(fill='x', pady=(8, 16))

        buttons = tk.Frame(slider_frame, bg=self.theme['panel'])
        buttons.pack(fill='x', pady=4)
        self._button(buttons, 'Forward', lambda: self.drive(1.0, 0.0)).grid(row=0, column=1, padx=5, pady=5)
        self._button(buttons, 'Left', lambda: self.drive(0.35, 0.8)).grid(row=1, column=0, padx=5, pady=5)
        self._button(buttons, 'Stop', self.stop).grid(row=1, column=1, padx=5, pady=5)
        self._button(buttons, 'Right', lambda: self.drive(0.35, -0.8)).grid(row=1, column=2, padx=5, pady=5)
        self._button(buttons, 'Reverse', lambda: self.drive(-0.5, 0.0)).grid(row=2, column=1, padx=5, pady=5)

        actions = tk.Frame(slider_frame, bg=self.theme['panel'])
        actions.pack(fill='x', pady=(16, 4))
        self._button(actions, 'EMERGENCY STOP', lambda: self.publish_estop(True), bg=self.theme['bad']).pack(fill='x', pady=(0, 6))
        self._button(actions, 'RESUME', lambda: self.publish_estop(False), bg=self.theme['good']).pack(fill='x')

        self.mission_text = tk.StringVar(value='Waiting for rover telemetry...')
        self.mission_box = tk.Label(
            state.content,
            textvariable=self.mission_text,
            bg=self.theme['panel_alt'],
            fg=self.theme['text'],
            justify='left',
            anchor='nw',
            wraplength=420,
            padx=12,
            pady=12,
        )
        self.mission_box.pack(fill='both', expand=True, padx=12, pady=12)

    def _bind_keys(self):
        self.root.bind('<space>', lambda event: self.publish_estop(True))
        self.root.bind('<Escape>', lambda event: self.stop())
        self.root.bind('w', lambda event: self.drive(1.0, 0.0))
        self.root.bind('s', lambda event: self.drive(-0.5, 0.0))
        self.root.bind('a', lambda event: self.drive(0.35, 0.8))
        self.root.bind('d', lambda event: self.drive(0.35, -0.8))

    def on_speed_change(self, value):
        self.node.speed_scale = float(value)

    def drive(self, forward_factor, turn_factor):
        speed = self.node.speed_scale
        self.node.publish_twist(linear=forward_factor * speed, angular=turn_factor * speed)

    def stop(self):
        self.node.publish_twist(0.0, 0.0)

    def publish_estop(self, active):
        self.node.publish_estop(active)
        self.append_log('Emergency stop triggered.' if active else 'Emergency stop cleared.')

    def append_log(self, message):
        self.event_history.append(f'[{datetime.now().strftime("%H:%M:%S")}] {message}')
        self.event_history = self.event_history[-8:]

    def _render_mission_box(self):
        mission_lines = [
            self._format_mission_state(),
            '',
            'Recent events:',
            *self.event_history,
        ]
        self.mission_text.set('\n'.join(mission_lines))

    def _update_camera(self):
        frame = self.node.state.camera_frame
        if frame is None:
            return

        try:
            preview = cv2.resize(frame, (640, 360))
            success, buffer = cv2.imencode('.png', preview)
            if success:
                encoded = base64.b64encode(buffer.tobytes()).decode('ascii')
                self.current_photo = tk.PhotoImage(data=encoded, format='PNG')
                self.camera_label.configure(image=self.current_photo, text='')
                return
        except Exception as exc:
            self.node.get_logger().warn(f'Camera preview update failed: {exc}')

        self.camera_label.configure(text='Camera feed active (preview decode fallback)', fg=self.theme['text'], bg='#000000', image='')

    def _update_scan(self):
        scan = self.node.state.scan
        self.scan_canvas.delete('all')
        width = max(20, self.scan_canvas.winfo_width())
        height = max(20, self.scan_canvas.winfo_height())
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) * 0.35

        self.scan_canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, outline='#253246')
        self.scan_canvas.create_line(center_x - radius, center_y, center_x + radius, center_y, fill='#253246')
        self.scan_canvas.create_line(center_x, center_y - radius, center_x, center_y + radius, fill='#253246')

        if scan is None or not scan.ranges:
            self.scan_canvas.create_text(
                center_x,
                center_y,
                text='Waiting for /scan...',
                fill=self.theme['muted'],
                font=('TkDefaultFont', 11),
            )
            return

        total = len(scan.ranges)
        step = max(1, total // 180)
        max_range = max(scan.range_max or 10.0, 1.0)
        for index, distance in enumerate(scan.ranges[::step]):
            if not math.isfinite(distance):
                distance = max_range
            actual_index = index * step
            angle = scan.angle_min + actual_index * scan.angle_increment
            clipped = max(0.0, min(distance, max_range))
            scaled = radius * (clipped / max_range)
            x = center_x + scaled * math.cos(angle)
            y = center_y - scaled * math.sin(angle)
            self.scan_canvas.create_line(center_x, center_y, x, y, fill=self.theme['accent'])

        min_range = min((r for r in scan.ranges if math.isfinite(r)), default=float('inf'))
        if math.isfinite(min_range):
            msg = f'Nearest obstacle: {min_range:0.2f} m'
        else:
            msg = 'Nearest obstacle: none in range'
        self.scan_canvas.create_text(10, 10, text=msg, fill=self.theme['text'], anchor='nw', font=('TkDefaultFont', 10, 'bold'))

    def _format_mission_state(self):
        scan = self.node.state.scan
        nearest = 'waiting for /scan'
        if scan is not None:
            finite_ranges = [r for r in scan.ranges if math.isfinite(r)]
            if finite_ranges:
                nearest = f'{min(finite_ranges):0.2f} m'
            else:
                nearest = 'clear'

        goal = self.node.state.goal_pose
        if goal is None:
            goal_text = 'No active waypoint'
        else:
            goal_text = f'Waypoint target: ({goal.pose.position.x:0.1f}, {goal.pose.position.y:0.1f})'

        return (
            f'State: {self.node.state.rover_status}\n'
            f'Terrain: {self.node.state.terrain_type}\n'
            f'Speed: {self.node.state.speed_mps:0.2f} m/s\n'
            f'LIDAR: nearest obstacle {nearest}. The plot is a top-down ring around the rover.\n'
            f'{goal_text}\n'
            f'E-Stop: {"ACTIVE" if self.node.state.estop_active else "CLEAR"}'
        )

    def _log_state_changes(self):
        snapshot = {
            'status': self.node.state.rover_status,
            'terrain': self.node.state.terrain_type,
            'estop': self.node.state.estop_active,
            'goal': None if self.node.state.goal_pose is None else (
                round(self.node.state.goal_pose.pose.position.x, 1),
                round(self.node.state.goal_pose.pose.position.y, 1),
            ),
        }
        if snapshot == self.last_log_snapshot:
            return

        self.last_log_snapshot = snapshot
        self.append_log(
            f'Status={snapshot["status"]}, terrain={snapshot["terrain"]}, '
            f'estop={"ON" if snapshot["estop"] else "OFF"}'
        )

    def refresh_ui(self):
        self.clock_label.configure(text=datetime.now().strftime('%d %b %Y  %H:%M:%S'))
        self.status_value.configure(text=self.node.state.rover_status, fg=self._status_color(self.node.state.rover_status))
        self.terrain_value.configure(text=self.node.state.terrain_type, fg=self._terrain_color(self.node.state.terrain_type))
        self.estop_value.configure(text='ACTIVE' if self.node.state.estop_active else 'CLEAR', fg=self.theme['bad'] if self.node.state.estop_active else self.theme['good'])
        self.speed_value.configure(text=f'{self.node.state.speed_mps:0.2f} m/s')
        self.timer_value.configure(text=f'{time.monotonic() - self.node.mission_start:0.1f}s')
        self.waypoint_value.configure(text=f'{self.node.state.waypoint_index} / {self.node.state.waypoint_total}')

        goal = self.node.state.goal_pose
        self.goal_value.configure(text='--' if goal is None else f'({goal.pose.position.x:0.1f}, {goal.pose.position.y:0.1f})')
        self._render_mission_box()

        self._update_camera()
        self._update_scan()
        self._log_state_changes()
        self.root.after(120, self.refresh_ui)

    def _status_color(self, status):
        return {
            'MOVING': self.theme['good'],
            'RECOVERY': self.theme['warn'],
            'ERROR': self.theme['bad'],
            'STUCK': self.theme['bad'],
            'OBSTACLE_DETECTED': self.theme['warn'],
            'ESTOP': self.theme['bad'],
            'STOPPED': self.theme['info'],
        }.get(status, self.theme['text'])

    def _terrain_color(self, terrain):
        return {
            'ROCKY': self.theme['warn'],
            'FLAT': self.theme['good'],
            'CRATER': self.theme['bad'],
        }.get(terrain, self.theme['text'])

    def run(self):
        self.root.mainloop()


def main(args=None):
    rclpy.init(args=args)
    node = DashboardNode()
    node.get_logger().info('Starting Tk dashboard window')
    node.get_logger().info(f'DISPLAY={os.environ.get("DISPLAY", "")}, WAYLAND_DISPLAY={os.environ.get("WAYLAND_DISPLAY", "")}')
    if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
        node.get_logger().warn('No display session detected; the dashboard window cannot be shown in this environment.')
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        RoverDashboardApp(node).run()
    except tk.TclError as exc:
        node.get_logger().error(f'Dashboard UI failed to start: {exc}')
    finally:
        node.destroy_node()
        rclpy.shutdown()

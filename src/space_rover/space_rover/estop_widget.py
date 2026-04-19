import threading
import tkinter as tk
from datetime import datetime

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String


class EstopWidgetNode(Node):
    def __init__(self):
        super().__init__('estop_widget')
        self.estop_pub = self.create_publisher(Bool, '/emergency_stop', 10)
        self.status_text = 'CLEAR'
        self.create_subscription(String, '/rover_status', self.status_callback, 10)

    def status_callback(self, msg):
        self.status_text = msg.data

    def publish_estop(self, active):
        self.estop_pub.publish(Bool(data=active))


class EstopWidgetApp:
    def __init__(self, node):
        self.node = node
        self.root = tk.Tk()
        self.root.title('E-Stop Widget')
        self.root.geometry('420x240')
        self.root.configure(bg='#130b0f')

        tk.Label(self.root, text='Emergency Stop', fg='#fff3f5', bg='#130b0f', font=('TkDefaultFont', 20, 'bold')).pack(pady=(18, 8))
        self.status = tk.Label(self.root, text='Rover status: --', fg='#f5a524', bg='#130b0f', font=('TkDefaultFont', 12))
        self.status.pack(pady=4)

        tk.Button(self.root, text='TRIGGER ESTOP', command=self.trigger, bg='#ff5c6c', fg='#130b0f', font=('TkDefaultFont', 12, 'bold'), padx=14, pady=10).pack(fill='x', padx=24, pady=(16, 8))
        tk.Button(self.root, text='CLEAR ESTOP', command=self.clear, bg='#2fd67b', fg='#130b0f', font=('TkDefaultFont', 12, 'bold'), padx=14, pady=10).pack(fill='x', padx=24)

        self.root.bind('<space>', lambda event: self.trigger())
        self.root.after(100, self.refresh)

    def trigger(self):
        self.node.publish_estop(True)

    def clear(self):
        self.node.publish_estop(False)

    def refresh(self):
        self.status.configure(text=f'Rover status: {self.node.status_text}  |  {datetime.now().strftime("%H:%M:%S")}')
        self.root.after(150, self.refresh)

    def run(self):
        self.root.mainloop()


def main(args=None):
    rclpy.init(args=args)
    node = EstopWidgetNode()
    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()

    try:
        EstopWidgetApp(node).run()
    finally:
        node.destroy_node()
        rclpy.shutdown()

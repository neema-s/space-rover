# 🚀 Space Rover Simulation (ROS 2 + Gazebo)

## Overview

This project implements a **simulated space rover** in a Mars-like environment using **ROS 2 (Humble)** and **Gazebo**. The rover is capable of **goal-based navigation**, **obstacle avoidance**, and **sensor-driven decision making**, with a supporting UI for monitoring and control.

The system demonstrates a **semi-autonomous robotic architecture**, combining **manual teleoperation** and **autonomous navigation**.

---

## Key Features

* Goal-based autonomous navigation
* LIDAR-based obstacle detection and avoidance
* Watchdog system for stuck detection and recovery
* Sensor integration (LIDAR, IMU, Camera)
* Dashboard UI for monitoring and manual control
* Modular ROS2 node architecture

---

## ⚙️ System Architecture

```text
UI → /goal_pose
        ↓
     nav_node
        ↓
     /cmd_vel
        ↓
     Rover (Gazebo)

Sensors:
LIDAR → obstacle_avoidance → nav_node  
IMU → nav_node  
Watchdog → nav_node
```

---
### Algorithm Used:

* **Proportional Controller (P-Control)**
* **Heading-based goal tracking**
* **Reactive obstacle avoidance**

---

## 🖥️ UI Features

* Manual control (Forward, Left, Right, Reverse)
* Emergency stop system
* Sensor visualization (camera, LIDAR)
* Rover status display

---

## 📊 Results

The rover successfully demonstrates:

* Autonomous movement toward a goal
* Obstacle detection
* Smooth avoidance behavior
* Recovery from stuck situations

---

## 🔮 Future Improvements

* Integrate Nav2 stack
* Add SLAM-based mapping
* Implement global path planning
* Improve obstacle avoidance (vector-based)
* Add UI-based goal input

---

## 🧪 How to Run

```bash
cd ~/mar_finalproj/space-rover
colcon build --symlink-install
source install/setup.bash
ros2 launch space_rover rover_sim.launch.py
```

### Send Goal:

```bash
ros2 topic pub /goal_pose geometry_msgs/PoseStamped \
"{header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 2.0}, orientation: {w: 1.0}}}"
```

---

## 🧠 Key Takeaways

* Designed a **navigation system from scratch**
* Implemented **sensor-driven decision making**
* Built a **modular ROS2 architecture**
* Solved **control conflicts and system integration challenges**

---

## 📌 Conclusion

This project demonstrates a **functional semi-autonomous rover system**, capable of navigating a simulated environment using real-time feedback and control logic. The navigation system forms the core of the rover, enabling intelligent movement and interaction with the environment.

---

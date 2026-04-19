Space Rover ROS2 Package

Overview
- This package launches a Gazebo-based Mars rover simulation and a ROS2 control stack.
- The stack includes navigation, obstacle avoidance, watchdog recovery, sensor bridges, terrain classification, mission logging, and operator UI.

Primary Launch
- launch/rover_sim.launch.py

Runtime Nodes
- Sensors: camera_node, lidar_node, imu_node, estop_node, terrain_classifier
- Navigation: nav_node, obstacle_avoidance, watchdog_node
- Status and telemetry: rover_status, mission_logger
- UI: dashboard, estop_widget

Key Topics
- /cmd_vel: rover motion command
- /odom: rover odometry
- /scan: lidar stream
- /camera/image_raw: camera stream
- /imu/data: imu stream
- /terrain_type: inferred terrain label
- /rover_status: consolidated rover state
- /emergency_stop: estop signal

Notes
- The launch flow starts runtime nodes only after the spawn process exits.
- Sensor plugins publish to raw gazebo topics and dedicated bridge nodes republish to app-facing topics.

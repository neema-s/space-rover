# Space Rover Demo Runbook (Team Copy-Paste)

Use this file exactly as written.

- Run each section in a separate terminal.
- Keep Terminal 1 running during the demo.
- Open normal bash terminals (not python terminals).

## Terminal 1 - Clean old processes, build, launch

```bash
cd ~/mar_project/space-rover

# Clean leftover ROS/Gazebo processes from previous runs
pkill -9 -f "ros2 launch space_rover rover_sim.launch.py" || true
pkill -9 -f gzserver || true
pkill -9 -f gzclient || true
pkill -9 -f "gazebo --verbose" || true
pkill -9 -f spawn_entity.py || true
pkill -9 -f robot_state_publisher || true

# Build
source /opt/ros/humble/setup.bash
colcon build --packages-select space_rover --symlink-install

# Launch (leave this terminal running)
source install/setup.bash
ros2 launch space_rover rover_sim.launch.py
```

Expected launch signs:

- Spawn status says successfully spawned entity rover.
- Nodes for dashboard and estop_widget start.

## Terminal 2 - Package and node checks

```bash
cd ~/mar_project/space-rover
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 pkg list | grep '^space_rover$'
ros2 node list | grep -E '^/gazebo$|^/dashboard$|^/estop_widget$|^/camera_node$|^/lidar_node$|^/imu_node$|^/nav_node$|^/obstacle_avoidance$|^/rover_status$'
```

## Terminal 3 - Topic presence

```bash
cd ~/mar_project/space-rover
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 topic list | grep -E '^/camera/image_raw$|^/scan$|^/imu/data$|^/rover_status$|^/terrain_type$'
```

## Terminal 4 - LIDAR sample

```bash
cd ~/mar_project/space-rover
source /opt/ros/humble/setup.bash
source install/setup.bash

timeout 15s ros2 topic echo /scan --once --qos-profile sensor_data --spin-time 5 --no-daemon
```

## Terminal 5 - Rover status sample

```bash
cd ~/mar_project/space-rover
source /opt/ros/humble/setup.bash
source install/setup.bash

timeout 15s ros2 topic echo /rover_status --once --spin-time 5 --no-daemon
```

## Terminal 6 - Terrain sample

```bash
cd ~/mar_project/space-rover
source /opt/ros/humble/setup.bash
source install/setup.bash

timeout 15s ros2 topic echo /terrain_type --once --spin-time 5 --no-daemon
```

## Terminal 7 - Camera rate

```bash
cd ~/mar_project/space-rover
source /opt/ros/humble/setup.bash
source install/setup.bash

timeout 12s ros2 topic hz /camera/image_raw
```

## If topic echo shows no output

Run this once in a new terminal, then rerun Terminals 4 to 7:

```bash
cd ~/mar_project/space-rover
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 daemon stop
ros2 daemon start
```

## End demo (cleanup)

```bash
pkill -9 -f "ros2 launch space_rover rover_sim.launch.py" || true
pkill -9 -f gzserver || true
pkill -9 -f gzclient || true
```


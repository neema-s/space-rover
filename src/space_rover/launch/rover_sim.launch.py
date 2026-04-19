from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, DeclareLaunchArgument, TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
import os
import tempfile
from ament_index_python.packages import get_package_share_directory
import xacro

def generate_launch_description():

    pkg_path = get_package_share_directory('space_rover')
    urdf_file = os.path.join(pkg_path, 'urdf', 'rover.urdf.xacro')
    world_file = os.path.join(pkg_path, 'worlds', 'mars_terrain.world')

    doc = xacro.process_file(urdf_file)
    robot_desc = doc.toxml()

    # Write the processed URDF once so spawn_entity does not depend on topic QoS timing.
    with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as tmp_urdf:
        tmp_urdf.write(robot_desc)
        urdf_spawn_file = tmp_urdf.name

    namespace = LaunchConfiguration('namespace', default='')

    spawn_rover = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        namespace=namespace,
        arguments=[
            '-entity', 'rover',
            '-file', urdf_spawn_file,
            '-timeout', '180.0',
            '-x', '0',
            '-y', '0',
            '-z', '1.2',
            '-unpause'
        ],
        output='screen'
    )

    rover_runtime_nodes = [
        Node(
            package='space_rover',
            executable='lidar_node',
            name='lidar_node',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='camera_node',
            name='camera_node',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='imu_node',
            name='imu_node',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='estop_node',
            name='estop_node',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='nav_node',
            name='nav_node',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='obstacle_avoidance',
            name='obstacle_avoidance',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='watchdog_node',
            name='watchdog_node',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='terrain_classifier',
            name='terrain_classifier',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='rover_status',
            name='rover_status',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='mission_logger',
            name='mission_logger',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='dashboard',
            name='dashboard',
            namespace=namespace,
            output='screen'
        ),

        Node(
            package='space_rover',
            executable='estop_widget',
            name='estop_widget',
            namespace=namespace,
            output='screen'
        ),
    ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Namespace to apply to all nodes (avoid duplicate node names)'
        ),

        # 🌍 Launch Gazebo (server + client) with required ROS plugins.
        ExecuteProcess(
            cmd=[
                'gazebo',
                '--verbose',
                world_file,
                '-s', 'libgazebo_ros_init.so',
                '-s', 'libgazebo_ros_factory.so'
            ],
            output='screen'
        ),

        # 🤖 Robot state publisher
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            namespace=namespace,
            parameters=[{
                "robot_description": robot_desc
            }]
        ),

        # Spawn rover first.
        spawn_rover,

        # Start runtime nodes only after spawn process exits.
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_rover,
                on_exit=[
                    TimerAction(
                        period=1.0,
                        actions=rover_runtime_nodes,
                    )
                ],
            )
        ),
    ])
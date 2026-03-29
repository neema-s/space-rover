from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os
from ament_index_python.packages import get_package_share_directory
import xacro

def generate_launch_description():

    pkg_path = get_package_share_directory('space_rover')
    urdf_file = os.path.join(pkg_path, 'urdf', 'rover.urdf.xacro')
    world_file = os.path.join(pkg_path, 'worlds', 'mars_terrain.world')

    doc = xacro.process_file(urdf_file)
    robot_desc = doc.toxml()

    namespace = LaunchConfiguration('namespace', default='')

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Namespace to apply to all nodes (avoid duplicate node names)'
        ),

        # 🌍 Launch Gazebo
        ExecuteProcess(
            cmd=[
                'gazebo',
                '--verbose',
                world_file,
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

        # 🚀 Spawn rover
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            namespace=namespace,
            arguments=[
                '-entity', 'rover',
                '-topic', 'robot_description',
                '-x', '0',
                '-y', '0',
                '-z', '0.5'
            ],
            output='screen'
        ),

        # 🔵 P2 NODES (ADD THESE)

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
    ])
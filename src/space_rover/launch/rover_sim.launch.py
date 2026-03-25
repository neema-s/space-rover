from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
import os
from ament_index_python.packages import get_package_share_directory
import xacro

def generate_launch_description():

    pkg_path = get_package_share_directory('space_rover')
    urdf_file = os.path.join(pkg_path, 'urdf', 'rover.urdf.xacro')
    world_file = os.path.join(pkg_path, 'worlds', 'mars_terrain.world')

    doc = xacro.process_file(urdf_file)
    robot_desc = doc.toxml()

    return LaunchDescription([

        ExecuteProcess(
            cmd=[
                'gazebo',
                '--verbose',
                world_file,
                '-s', 'libgazebo_ros_factory.so'
            ],
            output='screen'
        ),

        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{
                "robot_description": robot_desc
            }]
        ),

        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', 'rover',
                '-topic', 'robot_description',
                '-x', '0',
                '-y', '0',
                '-z', '0.5'
            ],
            output='screen'
        )
    ])

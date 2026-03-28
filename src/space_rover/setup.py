from setuptools import setup
from glob import glob

package_name = 'space_rover'

setup(
    name=package_name,
    version='0.0.0',

    packages=[
        'space_rover',
        'space_rover.sensors',
        'space_rover.navigation',
    ],

    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ] + [
        ('share/' + package_name + '/launch', glob('launch/*')),
        ('share/' + package_name + '/urdf', glob('urdf/*')),
        ('share/' + package_name + '/worlds', glob('worlds/*')),
        ('share/' + package_name + '/config', glob('config/*')),
    ],

    install_requires=['setuptools'],
    zip_safe=True,

    maintainer='your_name',
    maintainer_email='your_email',
    description='Space Rover',
    license='Apache License 2.0',

    entry_points={
        'console_scripts': [
            'nav_node = space_rover.navigation.nav_node:main',
            'lidar_node = space_rover.sensors.lidar_node:main',
            'camera_node = space_rover.sensors.camera_node:main',
            'imu_node = space_rover.sensors.imu_node:main',
            'estop_node = space_rover.sensors.estop_node:main',
            'dashboard = space_rover.dashboard:main',
            'mission_logger = space_rover.mission_logger:main',
            'estop_widget = space_rover.estop_widget:main',
            'rover_status = space_rover.rover_status_node:main',
            'test_node = space_rover.test_node:main',
        ],
    },
)
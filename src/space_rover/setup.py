setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/rover_sim.launch.py']),
        ('share/' + package_name + '/urdf', [
            'urdf/rover.urdf.xacro',
            'urdf/rover.gazebo'
        ]),
        ('share/' + package_name + '/worlds', ['worlds/mars_terrain.world']),
    ],
    entry_points={
        'console_scripts': [
            'dashboard        = space_rover.dashboard:main',
            'mission_logger   = space_rover.mission_logger:main',
            'estop_widget     = space_rover.estop_widget:main',
            'rover_status     = space_rover.rover_status_node:main',
        ],
    },
)

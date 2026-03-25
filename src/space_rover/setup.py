from setuptools import setup

package_name = 'space_rover'

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

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='neema-s',
    maintainer_email='shrivastavaneema@gmail.com',
    description='Space rover project',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
)

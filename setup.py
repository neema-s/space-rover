from setuptools import setup

package_name = 'space_rover'

setup(
    name=package_name,
    version='0.0.0',
    packages=['space_rover', 'space_rover.navigation'],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email',
    description='Space rover navigation package',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'nav_node = space_rover.navigation.nav_node:main',
        ],
    },
)

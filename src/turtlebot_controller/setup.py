from setuptools import find_packages, setup
from glob import glob

package_name = 'turtlebot_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/maps', glob('maps/*')),
        ('share/' + package_name + '/params', glob('params/*')),
        ('share/' + package_name + '/urdf', glob('urdf/*')),
        ('share/' + package_name + '/worlds', glob('worlds/*')),
        ('share/' + package_name + '/rviz', glob('rviz/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ste',
    maintainer_email='ste@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
	entry_points={
	    'console_scripts': [
	        'move_turtle = script_python.move_turtle:main',
            'move_turtle_AB = script_python.move_turtle_AB:main',
            'turtle_distance_publisher = script_python.turtle_distance_publisher:main',
            'turtle_csv_handler = script_python.turtle_csv_handler:main',
            'turtle_move_status_data = script_python.turtle_data.turtle_move_status_data:main',
            'turtle_position_data = script_python.turtle_data.turtle_position_data:main',
            'turtle_velocity_data = script_python.turtle_data.turtle_velocity_data:main'
    		],
	},

)

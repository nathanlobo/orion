from glob import glob

from setuptools import find_packages, setup

package_name = 'camera_system'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools', 'mediapipe', 'numpy'],
    zip_safe=True,
    maintainer='Nathan Francisco Lobo',
    maintainer_email='lobonathan2209@gmail.com',
    description='ROS 2 webcam streaming and MediaPipe face detection',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_node = camera_system.camera_node:main'
        ],
    },
)

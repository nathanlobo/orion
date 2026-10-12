import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('humanoid_voice')
    gazebo_share = get_package_share_directory('ros_gz_sim')
    world_path = os.path.join(package_share, 'worlds', 'voice_test_world.sdf')
    model_path = os.path.join(package_share, 'models', 'voice_test_bot.sdf')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r -v 3 {world_path}'}.items(),
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-world', 'voice_test_world',
            '-file', model_path,
            '-name', 'voice_test_bot',
        ],
        output='screen',
    )

    return LaunchDescription([
        gazebo,
        TimerAction(period=3.0, actions=[spawn_robot]),
    ])

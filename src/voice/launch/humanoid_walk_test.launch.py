import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


JOINTS = (
    'left_hip_roll',
    'left_hip_pitch',
    'left_knee',
    'left_ankle_pitch',
    'right_hip_roll',
    'right_hip_pitch',
    'right_knee',
    'right_ankle_pitch',
)


def generate_launch_description():
    package_share = get_package_share_directory('humanoid_voice')
    gazebo_share = get_package_share_directory('ros_gz_sim')
    world_path = os.path.join(package_share, 'worlds', 'voice_test_world.sdf')
    model_path = os.path.join(package_share, 'models', 'humanoid_walk_test.sdf')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r -v 3 {world_path}'}.items(),
    )

    spawn_humanoid = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-world', 'voice_test_world',
            '-file', model_path,
            '-name', 'humanoid_test',
            '-z', '0.80',
        ],
        output='screen',
    )

    joint_bridges = [
        f'/humanoid_test/{joint}/cmd_pos'
        '@std_msgs/msg/Float64]gz.msgs.Double'
        for joint in JOINTS
    ]
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=joint_bridges,
        output='screen',
    )

    return LaunchDescription([
        gazebo,
        bridge,
        TimerAction(
            period=4.0,
            actions=[spawn_humanoid],
        ),
    ])

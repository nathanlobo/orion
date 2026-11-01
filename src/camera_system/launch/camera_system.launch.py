from pathlib import Path

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    LogInfo,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    camera_node = Node(
        package='camera_system',
        executable='camera_node',
        name='camera_node',
        parameters=[{
            'face_model_path': LaunchConfiguration('face_model_path'),
        }],
        output='screen',
        emulate_tty=True,
    )
    preview_node = Node(
        package='rqt_image_view',
        executable='rqt_image_view',
        name='camera_preview',
        output='screen',
        emulate_tty=True,
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'face_model_path',
            default_value=str(
                Path.home() / '.ros' / 'models' / 'blaze_face_full_range.tflite'
            ),
            description='Path to the MediaPipe face detector TFLite model',
        ),
        camera_node,
        preview_node,
        RegisterEventHandler(
            OnProcessExit(
                target_action=camera_node,
                on_exit=[
                    LogInfo(msg='Camera node exited; stopping camera system launch.'),
                    EmitEvent(event=Shutdown(reason='camera node exited')),
                ],
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=preview_node,
                on_exit=[
                    LogInfo(msg='Camera preview exited; stopping camera system launch.'),
                    EmitEvent(event=Shutdown(reason='camera preview exited')),
                ],
            )
        ),
    ])

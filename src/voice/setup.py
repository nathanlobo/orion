from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'orion_voice'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py'),
        ),
        (
            os.path.join('share', package_name, 'models'),
            glob('models/*.sdf'),
        ),
        (
            os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.sdf'),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nathanlobo',
    maintainer_email='nathanlobo@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'audio_simulator = voice.audio_publisher:main',
            'wake_word = voice.wake_word_node:main',
            'llm_brain = voice.llm_node:main',
            'tts_node = voice.tts_node:main',
            'mic_publisher = voice.mic_publisher:main',
            'audio_receiver = voice.audio_receiver_node:main',
            'command_parser = voice.command_parser:main',
        ],
    },
)

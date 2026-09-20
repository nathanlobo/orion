from setuptools import find_packages, setup

package_name = 'humanoid_voice'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
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
        'audio_simulator = humanoid_voice.audio_publisher:main',
	    'wake_word = humanoid_voice.wake_word_node:main',
	    'llm_brain = humanoid_voice.llm_node:main',
	    'tts_node = humanoid_voice.tts_node:main',
        'mic_publisher = humanoid_voice.mic_publisher:main',
        'audio_receiver = humanoid_voice.audio_receiver_node:main',
        'command_parser = humanoid_voice.command_parser:main',
        ],
    },
)

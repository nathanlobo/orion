import math
import select
import sys
import termios
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64


class HumanoidWalkTest(Node):
    def __init__(self):
        super().__init__('humanoid_walk_test')
        self.period = 3.6
        self.elapsed = 0.0
        self.mode = 'stopped'
        self.direction = 1.0
        self.turn = 0.0
        self.quit_requested = False
        self.joint_publishers = {
            name: self.create_publisher(
                Float64,
                f'/humanoid_test/{name}/cmd_pos',
                10,
            )
            for name in (
                'left_hip_roll',
                'left_hip_pitch',
                'left_knee',
                'left_ankle_pitch',
                'right_hip_roll',
                'right_hip_pitch',
                'right_knee',
                'right_ankle_pitch',
            )
        }
        self.timer = self.create_timer(0.02, self.update)

    def update(self):
        self.read_keyboard()
        self.publish_pose()

    def read_keyboard(self):
        while select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1).lower()
            if key == 'w':
                self.mode = 'walking'
                self.direction = 1.0
                self.turn = 0.0
                print('Walking forward')
            elif key == 's':
                self.mode = 'walking'
                self.direction = -1.0
                self.turn = 0.0
                print('Walking backward')
            elif key == 'a':
                self.mode = 'walking'
                self.direction = 1.0
                self.turn = -0.35
                print('Walking with left-turn stride bias')
            elif key == 'd':
                self.mode = 'walking'
                self.direction = 1.0
                self.turn = 0.35
                print('Walking with right-turn stride bias')
            elif key == ' ':
                self.mode = 'stopped'
                self.turn = 0.0
                print('Holding neutral pose')
            elif key == 'q':
                self.mode = 'stopped'
                self.turn = 0.0
                self.quit_requested = True
                print('Exiting keyboard controller')

    def publish_pose(self):
        phase = 2.0 * math.pi * self.elapsed / self.period
        left_phase = phase
        right_phase = phase + math.pi

        if self.mode == 'stopped':
            positions = {
                'left_hip_roll': 0.0,
                'left_hip_pitch': 0.0,
                'left_knee': 0.08,
                'left_ankle_pitch': -0.03,
                'right_hip_roll': 0.0,
                'right_hip_pitch': 0.0,
                'right_knee': 0.08,
                'right_ankle_pitch': -0.03,
            }
        else:
            left_stride = 1.0 + self.turn
            right_stride = 1.0 - self.turn
            left_hip = (
                -0.12 * left_stride * self.direction * math.sin(left_phase)
            )
            right_hip = (
                -0.12 * right_stride * self.direction * math.sin(right_phase)
            )
            left_knee = 0.20 * max(0.0, math.sin(left_phase))
            right_knee = 0.20 * max(0.0, math.sin(right_phase))
            positions = {
                'left_hip_roll': 0.035 * math.sin(phase),
                'left_hip_pitch': left_hip,
                'left_knee': left_knee,
                'left_ankle_pitch': -left_hip - left_knee,
                'right_hip_roll': -0.035 * math.sin(phase),
                'right_hip_pitch': right_hip,
                'right_knee': right_knee,
                'right_ankle_pitch': -right_hip - right_knee,
            }

        for name, position in positions.items():
            message = Float64()
            message.data = position
            self.joint_publishers[name].publish(message)

        if self.mode == 'walking':
            self.elapsed += 0.02


def main(args=None):
    rclpy.init(args=args)
    node = HumanoidWalkTest()
    if not sys.stdin.isatty():
        node.get_logger().error(
            'Keyboard control requires a terminal. Run this node directly in '
            'a terminal with ros2 run humanoid_voice humanoid_walk_test.'
        )
        node.destroy_node()
        rclpy.shutdown()
        return

    terminal_settings = termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setcbreak(sys.stdin.fileno())
        print(
            'Humanoid keyboard test: W forward | S backward | '
            'A/D turn bias | Space stand | Q quit'
        )
        print('Open-loop gait only; falls are expected. Voice control is separate.')
        while rclpy.ok() and not node.quit_requested:
            rclpy.spin_once(node, timeout_sec=0.02)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(
            sys.stdin.fileno(),
            termios.TCSADRAIN,
            terminal_settings,
        )
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

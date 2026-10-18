import os

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

# Physical/sim motion outputs are OFF by default. Set ORION_ENABLE_MOTION=1 to
# re-enable /cmd_vel + /robot_action publishing (real robot or sim actuators).
ENABLE_MOTION = os.environ.get('ORION_ENABLE_MOTION', '0') == '1'

class CommandParserNode(Node):
    def __init__(self):
        super().__init__('command_parser')

        # Subscriber for STT transcripts
        self.subscription = self.create_subscription(
            String,
            '/speech_to_text',
            self.stt_callback,
            10
        )

        # Publishers for velocity commands + action status (disabled unless opted in)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.action_pub = self.create_publisher(String, '/robot_action', 10)

        # Anything that is NOT a motion command is forwarded here so the LLM
        # can answer it conversationally (Ollama -> /llm_response -> tts_node).
        self.llm_pub = self.create_publisher(String, '/llm_prompt', 10)

        if ENABLE_MOTION:
            self.get_logger().warn('Motion outputs ENABLED: publishing /cmd_vel + /robot_action')
        else:
            self.get_logger().info('Motion outputs DISABLED (default): /cmd_vel + /robot_action NOT published. Set ORION_ENABLE_MOTION=1 to enable.')
        self.get_logger().info('Command Parser Node active. Listening on /speech_to_text...')

    def stt_callback(self, msg):
        text = msg.data.lower().strip()
        self.get_logger().info(f'Received Speech Input: "{text}"')

        cmd = Twist()
        action_msg = String()

        # --- Motion Intent Rules ---
        if any(k in text for k in ['walk forward', 'move forward', 'go forward', 'step forward']):
            cmd.linear.x = 0.3
            action_msg.data = "ACTION: MOVING_FORWARD"
            self.get_logger().info('Exec: Moving Forward (0.3 m/s)')

        elif any(k in text for k in ['walk backward', 'move back', 'go back', 'step back']):
            cmd.linear.x = -0.3
            action_msg.data = "ACTION: MOVING_BACKWARD"
            self.get_logger().info('Exec: Moving Backward (-0.3 m/s)')

        elif any(k in text for k in ['turn left', 'rotate left']):
            cmd.angular.z = 0.5
            action_msg.data = "ACTION: TURNING_LEFT"
            self.get_logger().info('Exec: Turning Left (0.5 rad/s)')

        elif any(k in text for k in ['turn right', 'rotate right']):
            cmd.angular.z = -0.5
            action_msg.data = "ACTION: TURNING_RIGHT"
            self.get_logger().info('Exec: Turning Right (-0.5 rad/s)')

        elif any(k in text for k in ['stop', 'halt', 'freeze', 'don\'t move']):
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            action_msg.data = "ACTION: STOPPED"
            self.get_logger().info('Exec: STOPPING ROBOT')

        elif 'wave' in text or 'hello' in text:
            # Greetings are conversational, not motion: let the LLM answer.
            # (Keeps the old gesture status for motion mode.)
            action_msg.data = "ACTION: GESTURE_WAVE"
            self.get_logger().info('Greeting heard: forwarding to LLM for a spoken reply')
            prompt = String()
            prompt.data = (
                "The user just said hello to you. "
                "Reply with a very short, one-sentence friendly greeting."
            )
            self.llm_pub.publish(prompt)
            if ENABLE_MOTION:
                self.cmd_vel_pub.publish(cmd)
                self.action_pub.publish(action_msg)
            else:
                self.get_logger().info(
                    f'Motion suppressed (ORION_ENABLE_MOTION=0): would have published {action_msg.data}'
                )
            return

        else:
            # Not a motion command -> conversational: forward the raw speech
            # to the LLM instead of dropping it as UNKNOWN_COMMAND.
            self.get_logger().info(f'Not a motion command, forwarding to LLM: "{text}"')
            prompt = String()
            prompt.data = (
                "Answer briefly in one or two short sentences. "
                f"User said: {msg.data.strip()}"
            )
            self.llm_pub.publish(prompt)
            return

        # Publish outputs
        if ENABLE_MOTION:
            self.cmd_vel_pub.publish(cmd)
            self.action_pub.publish(action_msg)
        else:
            self.get_logger().info(f'Motion suppressed (ORION_ENABLE_MOTION=0): would have published {action_msg.data}')

def main(args=None):
    rclpy.init(args=args)
    node = CommandParserNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
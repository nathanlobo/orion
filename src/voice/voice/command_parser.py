import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

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

        # Publisher for velocity commands (standard ROS 2 motion interface)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Publisher for action status strings
        self.action_pub = self.create_publisher(String, '/robot_action', 10)

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
            action_msg.data = "ACTION: GESTURE_WAVE"
            self.get_logger().info('Exec: Performing Wave Gesture')

        else:
            action_msg.data = f"UNKNOWN_COMMAND: {text}"
            self.get_logger().warn(f'No matching motion intent for: "{text}"')
            return

        # Publish outputs
        self.cmd_vel_pub.publish(cmd)
        self.action_pub.publish(action_msg)

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
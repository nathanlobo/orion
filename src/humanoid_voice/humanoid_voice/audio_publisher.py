
import rclpy
from rclpy.node import Node
from std_msgs.msg import String # We will use String for the mock, later ByteMultiArray for raw audio

class AudioSimulator(Node):
    def __init__(self):
        super().__init__('audio_simulator')
        # Create a publisher on the '/audio_in' topic
        self.publisher_ = self.create_publisher(String, '/audio_in', 10)
        # Timer to trigger the callback every 2 seconds
        self.timer = self.create_timer(2.0, self.publish_mock_audio)
        self.get_logger().info('Audio Simulator Node has started.')

    def publish_mock_audio(self):
        msg = String()
        msg.data = '[Mock Audio Data: "Hey Robot"]'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')

def main(args=None):
    rclpy.init(args=args)
    node = AudioSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

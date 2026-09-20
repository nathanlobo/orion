import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class WakeWordProcessor(Node):
    def __init__(self):
        super().__init__('wake_word_processor')
        # Listen to the microphone simulator
        self.subscription = self.create_subscription(
            String,
            '/audio_in',
            self.listener_callback,
            10)
        
        # Publish to the robot's brain
        self.llm_publisher = self.create_publisher(String, '/llm_prompt', 10)
        
        self.get_logger().info('Wake Word Processor is listening...')

    def listener_callback(self, msg):
        if "Hey Robot" in msg.data:
            self.get_logger().info('🔔 WAKE WORD DETECTED! Waking up the AI...')
            
            # Send a hardcoded system prompt to the LLM
            prompt_msg = String()
            prompt_msg.data = "You were just woken up by your human operator. Give a very short, one-sentence friendly greeting."
            self.llm_publisher.publish(prompt_msg)
        else:
            self.get_logger().info('Ignoring background noise...')

def main(args=None):
    rclpy.init(args=args)
    node = WakeWordProcessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

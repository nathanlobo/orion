import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess
import os

class TTSProcessor(Node):
    def __init__(self):
        super().__init__('tts_processor')
        self.subscription = self.create_subscription(
            String,
            '/llm_response',
            self.listener_callback,
            10)
        
        self.model_path = os.path.expanduser('~/humanoid_ws/models/en_US-lessac-low.onnx')
        self.get_logger().info('TTS Node initialized. Waiting for AI responses...')

    def listener_callback(self, msg):
        clean_text = msg.data.replace('"', '').replace('\n', ' ').strip()
        self.get_logger().info(f'Synthesizing speech for: "{clean_text}"')
        
        wav_path = "/tmp/robot_response.wav"
        
        try:
            piper_cmd = [
                'python3', '-m', 'piper', 
                '--model', self.model_path, 
                '--output_file', wav_path
            ]
            
            subprocess.run(piper_cmd, input=clean_text, text=True, check=True)
            
            self.get_logger().info('Speaking...')
            subprocess.run(['paplay', wav_path], check=True)
            
        except subprocess.CalledProcessError as e:
            self.get_logger().error(f'Audio pipeline failed: {e}')
        except Exception as e:
            self.get_logger().error(f'Unexpected error: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = TTSProcessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
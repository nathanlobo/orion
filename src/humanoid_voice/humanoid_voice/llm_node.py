import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import requests
import subprocess

class LLMProcessor(Node):
    def __init__(self):
        super().__init__('llm_processor')
        # Listen for prompts
        self.subscription = self.create_subscription(
            String,
            '/llm_prompt',
            self.prompt_callback,
            10)
        # Publish responses for the TTS to speak later
        self.publisher_ = self.create_publisher(String, '/llm_response', 10)
        
        # Dynamically find the Windows Host IP
        self.windows_ip = self.get_wsl_host_ip()
        self.get_logger().info(f'LLM Node connecting to Windows Ollama at {self.windows_ip}...')

    def get_wsl_host_ip(self):
        try:
            # Runs the 'ip route' command and extracts the gateway IP
            result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True)
            return result.stdout.split()[2]
        except Exception:
            return "127.0.0.1"

    def prompt_callback(self, msg):
        self.get_logger().info(f'Thinking about: "{msg.data}"')
        
        url = f"http://{self.windows_ip}:11434/api/generate"
        payload = {
            "model": "llama3.2:1b",
            "prompt": msg.data,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            # Check if Ollama returned an error (like a missing model)
            if 'error' in data:
                self.get_logger().error(f"Ollama API Error: {data['error']}")
                return
            
            response_text = data.get('response', '')
            self.get_logger().info(f'Response: {response_text}')
            
            out_msg = String()
            out_msg.data = response_text
            self.publisher_.publish(out_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to reach Windows Ollama: {e}')
        
        try:
            response = requests.post(url, json=payload)
            response_text = response.json().get('response', '')
            
            self.get_logger().info(f'Response: {response_text}')
            
            # Publish the response to the ROS 2 network
            out_msg = String()
            out_msg.data = response_text
            self.publisher_.publish(out_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to reach Windows Ollama: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = LLMProcessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

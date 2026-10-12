import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sounddevice as sd
import numpy as np

class MicPublisher(Node):
    def __init__(self):
        super().__init__('mic_publisher')
        self.publisher_ = self.create_publisher(String, '/audio_in', 10)
        
        # Audio configuration
        self.sample_rate = 16000  # Standard for speech processing (Whisper/openWakeWord)
        self.block_size = 4000    # Chunk size
        
        self.get_logger().info('Microphone Node initialized. Listening for live audio...')
        
        # Start the audio input stream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=self.audio_callback
        )
        self.stream.start()

    def audio_callback(self, indata, frames, time, status):
        if status:
            self.get_logger().warn(f'Audio status warning: {status}')
        
        # Convert audio chunk to a flat numpy array
        audio_data = indata.flatten()
        
        # Compute volume level to detect speech activity
        volume = np.linalg.norm(audio_data) * 10
        
        msg = String()
        # For now, if volume spikes above a speaking threshold, we simulate the wake word trigger 
        # or pass raw data characteristics. In the next upgrade, we will feed this directly into openWakeWord!
        if volume > 1.5:
            self.get_logger().info(f'Speech detected! (Volume: {volume:.2f})')
            msg.data = "[Live Speech: Hey Robot]"
        else:
            msg.data = "[Background Noise]"
            
        self.publisher_.publish(msg)

    def destroy_node(self):
        self.stream.stop()
        self.stream.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = MicPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
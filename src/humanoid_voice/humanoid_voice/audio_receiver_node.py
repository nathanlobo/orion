import socket
import threading
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from faster_whisper import WhisperModel

class FastAudioWhisperReceiverNode(Node):
    def __init__(self):
        super().__init__('audio_receiver')

        self.publisher_ = self.create_publisher(String, '/speech_to_text', 10)

        self.get_logger().info('Loading optimized faster-whisper model...')
        # CPU Optimization: set cpu_threads to 4 for faster inference
        self.model = WhisperModel('tiny.en', device='cpu', compute_type='int8', cpu_threads=4)
        self.get_logger().info('Whisper model loaded!')

        self.sample_rate = 16000
        self.audio_buffer = bytearray()
        
        # Raised threshold to ignore room noise
        self.speech_threshold = 0.04
        self.silence_chunks = 0
        # Reduced silence requirement to ~0.5s for fast response
        self.max_silence_chunks = 5
        # Cap max audio length to 5 seconds (16000 samples * 2 bytes * 5 = 160000 bytes)
        self.max_buffer_bytes = 160000

        self.host = '0.0.0.0'
        self.port = 50005
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)

        self.get_logger().info(f'Audio Receiver listening on port {self.port}...')
        self.thread = threading.Thread(target=self.listen_for_clients, daemon=True)
        self.thread.start()

    def listen_for_clients(self):
        while rclpy.ok():
            client_socket, addr = self.server_socket.accept()
            self.get_logger().info(f'Connected to Web Bridge at {addr}')
            self.handle_client(client_socket)

    def handle_client(self, client_socket):
        while rclpy.ok():
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                self.process_audio_chunk(data)
            except Exception as e:
                self.get_logger().error(f'Socket error: {e}')
                break
        client_socket.close()

    def process_audio_chunk(self, chunk):
        int_data = np.frombuffer(chunk, dtype=np.int16)
        if len(int_data) == 0:
            return

        float_data = int_data.astype(np.float32) / 32768.0
        rms = np.sqrt(np.mean(float_data ** 2))

        if rms > self.speech_threshold:
            self.audio_buffer.extend(chunk)
            self.silence_chunks = 0
            
            # Force transcription if user speaks continuously for > 5 seconds
            if len(self.audio_buffer) >= self.max_buffer_bytes:
                self.get_logger().info('Max buffer limit reached! Transcribing immediately...')
                self.run_whisper_inference()
        else:
            if len(self.audio_buffer) > 0:
                self.audio_buffer.extend(chunk)
                self.silence_chunks += 1

                if self.silence_chunks >= self.max_silence_chunks:
                    self.run_whisper_inference()

    def run_whisper_inference(self):
        if len(self.audio_buffer) < self.sample_rate * 2 * 0.4:  # Drop noise snippets under 0.4s
            self.audio_buffer = bytearray()
            self.silence_chunks = 0
            return

        pcm_array = np.frombuffer(self.audio_buffer, dtype=np.int16)
        float_audio = pcm_array.astype(np.float32) / 32768.0

        # Fast inference parameters
        segments, _ = self.model.transcribe(
            float_audio,
            beam_size=1,
            language='en',
            vad_filter=True  # Filter out non-speech artifacts automatically
        )
        transcription = " ".join([segment.text for segment in segments]).strip()

        if transcription:
            self.get_logger().info(f'>>> STT Output ({len(self.audio_buffer)} bytes): "{transcription}" <<<')
            msg = String()
            msg.data = transcription
            self.publisher_.publish(msg)

        self.audio_buffer = bytearray()
        self.silence_chunks = 0

def main(args=None):
    rclpy.init(args=args)
    node = FastAudioWhisperReceiverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
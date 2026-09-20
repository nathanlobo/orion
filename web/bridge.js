const { WebSocketServer } = require('ws');
const net = require('net');

const WS_PORT = 8080;
const WSL_IP = '127.0.0.1'; // Localhost since both ROS 2 and Node run inside WSL
const WSL_PORT = 50005;

const wss = new WebSocketServer({ port: WS_PORT, host: '0.0.0.0' });
console.log(`[Bridge] WebSocket server running on ws://0.0.0.0:${WS_PORT}`);

wss.on('connection', (ws) => {
  console.log('[Bridge] Dashboard connected!');

  // Connect to local ROS 2 audio_receiver node TCP socket
  const rosSocket = new net.Socket();
  rosSocket.connect(WSL_PORT, WSL_IP, () => {
    console.log(`[Bridge] Connected to ROS 2 receiver socket on port ${WSL_PORT}`);
  });

  rosSocket.on('error', (err) => {
    console.error('[Bridge] ROS 2 Socket Error:', err.message);
  });

  ws.on('message', (message) => {
    // Check if the TCP socket to ROS 2 is actually open and ready
    if (rosSocket.writable) {
      const success = rosSocket.write(Buffer.from(message));
      if (!success) {
        console.warn('[Bridge] ROS 2 socket buffer full / paused write');
      }
    } else {
      console.error('[Bridge] Cannot send chunk: ROS 2 TCP socket is CLOSED or NOT WRITABLE');
    }
  });

  ws.on('close', () => {
    console.log('[Bridge] Dashboard disconnected.');
    rosSocket.end();
  });
});
// Merged server: Next.js dashboard + mic-audio WebSocket bridge in one process.
// Browser connects to ws(s)://<same-host>/audio — no second port, no tunnel.
// Audio chunks are forwarded over TCP to the ROS 2 audio_receiver on 127.0.0.1:50005.
const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');
const { WebSocketServer } = require('ws');
const net = require('net');

const dev = process.env.NODE_ENV !== 'production';
const PORT = parseInt(process.env.PORT || '3000', 10);
const ROS_HOST = process.env.ROS_HOST || '127.0.0.1';
const ROS_PORT = parseInt(process.env.ROS_PORT || '50005', 10);

const app = next({ dev, dir: __dirname });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = createServer(async (req, res) => {
    try {
      const parsedUrl = parse(req.url, true);
      await handle(req, res, parsedUrl);
    } catch (err) {
      console.error('[Server] Request handler error:', err);
      res.statusCode = 500;
      res.end('Internal server error');
    }
  });

  const wss = new WebSocketServer({ noServer: true });
  console.log(`[Bridge] Audio WebSocket mounted at /audio (-> ${ROS_HOST}:${ROS_PORT})`);

  // Only handle upgrades for OUR path. Everything else (notably Next.js dev
  // HMR at /_next/webpack-hmr) must fall through to Next's own handler —
  // otherwise HMR breaks with "WebSocket connection to '.../_next/hmr' failed".
  server.on('upgrade', (req, socket, head) => {
    let pathname = '';
    try {
      pathname = parse(req.url || '').pathname || '';
    } catch {
      socket.destroy();
      return;
    }
    if (pathname !== '/audio') {
      return; // let Next.js handle its own upgrades
    }
    wss.handleUpgrade(req, socket, head, (ws) => {
      wss.emit('connection', ws, req);
    });
  });

  wss.on('connection', (ws) => {
    console.log('[Bridge] Dashboard connected!');

    const rosSocket = new net.Socket();
    rosSocket.connect(ROS_PORT, ROS_HOST, () => {
      console.log(`[Bridge] Connected to ROS 2 receiver socket on port ${ROS_PORT}`);
    });

    rosSocket.on('error', (err) => {
      console.error('[Bridge] ROS 2 Socket Error:', err.message);
    });

    ws.on('message', (message) => {
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

  server.listen(PORT, '0.0.0.0', () => {
    console.log(`[Server] Ready on http://0.0.0.0:${PORT} (${dev ? 'dev' : 'production'})`);
  });
});

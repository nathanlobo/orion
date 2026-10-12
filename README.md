# Humanoid Robot Voice Control System

An end-to-end voice command pipeline for a humanoid robot. A browser captures microphone audio and sends 16-bit PCM audio over WebSocket to a Node.js bridge. The bridge forwards the audio over TCP to a ROS 2 receiver, which transcribes it with faster-whisper. Recognized commands are converted into ROS 2 velocity and action messages.

## Architecture

```text
Browser microphone
       |
       | WSS through Cloudflare Tunnel
       v
Node.js WebSocket bridge (:8080)
       |
       | TCP
       v
ROS 2 audio_receiver (:50005)
       |
       | /speech_to_text
       v
ROS 2 command_parser
       |                         |
       | /cmd_vel                | /robot_action
       v                         v
Robot motion controller      Robot action state
```

The repository also contains separate wake-word, Ollama, and text-to-speech nodes. They are not required for the browser-to-`/cmd_vel` path and are described in [Optional ROS nodes](#optional-ros-nodes).

## Requirements

### Operating system

- Ubuntu 22.04 or 24.04
- Windows WSL2 with Ubuntu is supported
- A working microphone on the browser machine

### Software

- ROS 2 Humble, Jazzy, or Rolling
- `colcon`
- Python 3.10 or newer
- `python3-pip` and `python3-venv`
- Node.js 20.9 or newer and npm
- Gazebo Harmonic and the ROS-Gazebo integration (`ros-jazzy-ros-gz`) for simulation
- Cloudflare Tunnel (`cloudflared`) if the dashboard is accessed through a public HTTPS hostname

Next.js 16 requires Node.js 20.9 or newer. Node.js 18 is not sufficient for the current web dependencies.

## Clone the workspace

The TTS node currently expects the workspace at `~/humanoid_ws` because it uses `~/humanoid_ws/models/...` as a model path.

```bash
git clone <repository-url> ~/humanoid_ws
cd ~/humanoid_ws
```

If the workspace is stored elsewhere, update the model path in `src/voice/voice/tts_node.py` before using TTS.

## Install ROS and Python dependencies

Source ROS 2 in every terminal that runs a ROS command. Replace `jazzy` with the installed distribution.

```bash
source /opt/ros/jazzy/setup.bash
```

Install the ROS dependencies used by the nodes:

```bash
sudo apt update
sudo apt install -y \
  python3-pip \
  python3-full \
  python3-venv \
  portaudio19-dev \
  pulseaudio-utils \
  ros-jazzy-rclpy \
  ros-jazzy-std-msgs \
  ros-jazzy-geometry-msgs
```

Install the Python packages used by the audio receiver, microphone node, LLM node, and TTS node:

```bash
python3 -m pip install --user \
  faster-whisper \
  numpy \
  requests \
  sounddevice \
  piper-tts
```

If Ubuntu reports an externally managed environment, use a virtual environment or add `--break-system-packages` according to your team policy. ROS Python packages still need to be available in the sourced ROS environment.

The first start of `audio_receiver` downloads the faster-whisper `tiny.en` model. Internet access is required on that first run.

## Build the ROS 2 package

```bash
cd ~/humanoid_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select humanoid_voice
source install/setup.bash
```

After changing Python files, rebuild and source the workspace again:

```bash
colcon build --packages-select humanoid_voice
source install/setup.bash
```

## Install the web application

```bash
cd ~/humanoid_ws/web
npm install
```

The web application contains the dashboard and the WebSocket bridge:

- `npm run dev`: start the Next.js development server
- `npm run build`: create a production build
- `npm start`: serve a production build
- `node bridge.js`: start the WebSocket-to-TCP bridge

## Cloudflare Tunnel setup

The bridge listens on `0.0.0.0:8080`. Configure a Cloudflare Tunnel hostname to forward WebSocket traffic to that port. For example, the public bridge hostname used by the current dashboard is `bridge.codinx.app`.

The tunnel must:

1. Forward the public HTTPS/WSS hostname to the Node bridge at `http://localhost:8080`.
2. Allow WebSocket connections.
3. Run in an environment that can reach the Node bridge inside WSL.
4. Be running before the browser presses **Start Live Microphone Stream**.

The dashboard currently connects to `wss://bridge.codinx.app` in `web/app/page.tsx`. If your team uses another hostname, update that URL before starting the frontend.

For local-only testing, change the dashboard WebSocket URL to `ws://localhost:8080` and open the dashboard from a local HTTP origin. Microphone access still requires browser permission.

## Run the primary voice pipeline

Open four terminals. In each ROS terminal, source both ROS 2 and the workspace.

### Terminal 1: audio receiver and speech-to-text

```bash
cd ~/humanoid_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
PYTHONUNBUFFERED=1 ros2 run humanoid_voice audio_receiver
```

This node listens on TCP `0.0.0.0:50005`, detects speech and silence, transcribes English audio with faster-whisper, and publishes `/speech_to_text`.

### Terminal 2: command parser

```bash
cd ~/humanoid_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run humanoid_voice command_parser
```

This node converts supported transcript phrases into `/cmd_vel` and `/robot_action` messages.

### Terminal 3: WebSocket bridge

```bash
cd ~/humanoid_ws/web
node bridge.js
```

Expected bridge behavior:

- WebSocket server: `0.0.0.0:8080`
- ROS TCP destination: `127.0.0.1:50005`

The bridge and `audio_receiver` are configured to run in the same WSL environment. If they run on different machines, update the `WSL_IP` constant in `web/bridge.js` and open TCP port `50005` between them.

### Terminal 4: Next.js dashboard

```bash
cd ~/humanoid_ws/web
npm run dev
```

Open the URL printed by Next.js, usually `http://localhost:3000`, or open the public Cloudflare URL. Grant microphone permission, then click **Start Live Microphone Stream**.

## Verify the pipeline

Inspect speech transcripts:

```bash
ros2 topic echo /speech_to_text
```

Inspect velocity commands:

```bash
ros2 topic echo /cmd_vel
```

Inspect action states:

```bash
ros2 topic echo /robot_action
```

Useful checks:

```bash
ros2 topic list
ros2 node list
ss -ltn | grep -E '50005|8080'
```

The voice-command package publishes `/cmd_vel`, but it is not connected to Gazebo or a physical robot controller. The Gazebo test robot is operated separately through Gazebo Transport.

## Run the standalone Gazebo test

The project includes a small differential-drive robot as a standalone Gazebo test. It is not connected to the ROS voice nodes, their `/cmd_vel` topic, or a physical robot. Use `gz topic` commands to drive it directly through Gazebo Transport. It is a disposable test model, not a humanoid or a description of the final robot. The Gazebo DiffDrive system limits simulated speed to 0.5 m/s and turning speed to 1.0 rad/s.

Install Gazebo Harmonic and the ROS 2 Jazzy Gazebo integration if they are not already installed:

```bash
sudo apt update
sudo apt install -y ros-jazzy-ros-gz
```

Build and launch the simulator in one terminal:

```bash
cd ~/humanoid_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select humanoid_voice
source install/setup.bash
ros2 launch humanoid_voice voice_test_gazebo.launch.py
```

With Gazebo running, use Gazebo Transport to send commands directly to the simulated robot:

```bash
# Drive forward
gz topic -t /cmd_vel -m gz.msgs.Twist \
  -p "linear: {x: 0.3}, angular: {z: 0.0}"

# Turn in place
gz topic -t /cmd_vel -m gz.msgs.Twist \
  -p "linear: {x: 0.0}, angular: {z: 0.5}"

# Stop
gz topic -t /cmd_vel -m gz.msgs.Twist \
  -p "linear: {x: 0.0}, angular: {z: 0.0}"
```

These commands are sent to Gazebo Transport, not ROS 2; the simulation launch does not start a ROS-Gazebo bridge. Close the Gazebo launch process to stop the simulator. This is only a standalone model and basic drive test; voice control, ROS odometry, and the actual humanoid model are not part of this simulation setup.

## Experimental humanoid walking simulation

`humanoid_walk_test` launches a separate primitive humanoid biped in Gazebo. It is independent of the voice pipeline and does not use its `/cmd_vel` topic. A separate terminal node provides keyboard control over eight actuated leg joints. Its slower, smaller leg swings and ankle compensation are intended to reduce forward pitching, but the gait has no balance feedback, so the robot may still wobble or fall. This is not a validated walking controller or a model of the final robot.

Build the package:

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
colcon build --packages-select humanoid_voice
source install/setup.bash
```

In the first terminal, launch Gazebo and spawn the humanoid:

```bash
ros2 launch humanoid_voice humanoid_walk_test.launch.py
```

In a second sourced terminal, start keyboard control:

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run humanoid_voice humanoid_walk_test
```

Use these keys in the keyboard-controller terminal:

| Key | Action |
| --- | --- |
| `W` | Walk forward |
| `S` | Walk backward |
| `A` / `D` | Walk with an experimental left/right stride bias |
| `Space` | Stop gait and command a neutral leg pose |
| `Q` | Exit the keyboard controller; Gazebo stays open |

The left/right controls only bias the relative stride lengths; turning is not guaranteed. The gait is open-loop, so falling is expected. Closing the Gazebo terminal stops the simulation.

This simulation's ROS-Gazebo bridge only carries joint-position targets. It does not connect voice commands or `/cmd_vel`.

## Supported voice commands

The command parser lowercases and trims each transcript before matching it.

| Spoken phrase | Output |
| --- | --- |
| `walk forward`, `move forward`, `go forward`, `step forward` | `/cmd_vel.linear.x = 0.3` |
| `walk backward`, `move back`, `go back`, `step back` | `/cmd_vel.linear.x = -0.3` |
| `turn left`, `rotate left` | `/cmd_vel.angular.z = 0.5` |
| `turn right`, `rotate right` | `/cmd_vel.angular.z = -0.5` |
| `stop`, `halt`, `freeze`, `don't move` | Zero linear and angular velocity |
| Any phrase containing `wave` or `hello` | `/robot_action = ACTION: GESTURE_WAVE` |

Movement commands publish both a `geometry_msgs/msg/Twist` message on `/cmd_vel` and a status string on `/robot_action`. Unknown commands are logged but do not publish motion commands.

## ROS topics

| Topic | Type | Publisher | Subscriber | Purpose |
| --- | --- | --- | --- | --- |
| `/speech_to_text` | `std_msgs/msg/String` | `audio_receiver` | `command_parser` | Whisper transcript |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | `command_parser` | External robot controller | Motion command |
| `/robot_action` | `std_msgs/msg/String` | `command_parser` | External robot controller/UI | Action status |
| `/audio_in` | `std_msgs/msg/String` | `audio_simulator`, `mic_publisher` | `wake_word` | Simulated audio/wake-word input |
| `/llm_prompt` | `std_msgs/msg/String` | `wake_word` | `llm_brain` | Prompt for Ollama |
| `/llm_response` | `std_msgs/msg/String` | `llm_brain` | `tts_node` | Text for speech synthesis |

The browser sends raw PCM through the TCP receiver path; it does not publish raw audio to `/audio_in`.

## Optional ROS nodes

The package installs these additional executables:

| Executable | Purpose |
| --- | --- |
| `audio_simulator` | Publishes mock `Hey Robot` messages to `/audio_in` every two seconds |
| `mic_publisher` | Captures a local microphone and publishes simplified speech/noise strings to `/audio_in` |
| `wake_word` | Looks for the exact case-sensitive phrase `Hey Robot` and publishes a greeting prompt |
| `llm_brain` | Sends `/llm_prompt` to an Ollama server on the Windows host |
| `tts_node` | Synthesizes `/llm_response` with Piper and plays it with `paplay` |

### Ollama setup

To use `llm_brain`, install Ollama on the Windows host and pull the configured model:

```powershell
ollama pull llama3.2:1b
```

Ollama must accept requests from WSL on port `11434`. The node discovers the Windows host gateway with `ip route show default` and calls:

```text
http://<windows-host-ip>:11434/api/generate
```

### TTS setup

The repository expects these files:

```text
~/humanoid_ws/models/en_US-lessac-low.onnx
~/humanoid_ws/models/en_US-lessac-low.onnx.json
```

The TTS node invokes `python3 -m piper` and then `paplay`. WSL audio output must be configured for `paplay` to produce sound.

## Troubleshooting

### Browser says microphone permission was denied

Allow microphone access for the dashboard hostname in the browser and operating system privacy settings. Microphone capture requires a secure context, normally HTTPS for a public Cloudflare URL or localhost for local development.

### Browser cannot connect to the bridge

Check all of the following:

```bash
ss -ltn | grep 8080
```

- `node bridge.js` is running.
- The dashboard URL in `web/app/page.tsx` matches the Cloudflare hostname.
- The Cloudflare Tunnel forwards to port `8080` and supports WebSockets.
- The browser is using `wss://` for an HTTPS dashboard.

### Bridge cannot connect to ROS

Check the receiver first:

```bash
ss -ltn | grep 50005
```

Start `audio_receiver` before the bridge. If the processes are on different hosts, update `WSL_IP` in `web/bridge.js` and check firewall rules.

### No transcript is published

- Speak loudly enough to exceed the receiver RMS threshold.
- Speak English; the receiver is configured with `language='en'`.
- Speak for at least about 0.4 seconds and pause so the silence detector triggers transcription.
- Check the receiver logs for the faster-whisper model download or transcription errors.

### `/cmd_vel` is empty

Confirm that both nodes are running and that the transcript matches one of the supported phrases:

```bash
ros2 node list
ros2 topic echo /speech_to_text
ros2 topic echo /cmd_vel
```

### TTS does not play audio

Check that the model path exists and that `paplay` can play a local WAV file:

```bash
ls -l ~/humanoid_ws/models/en_US-lessac-low.onnx
which paplay
```

## Known limitations

- The browser endpoint is currently hardcoded to `wss://bridge.codinx.app`.
- The browser-to-ROS path uses the direct command parser; STT transcripts are not forwarded to `/llm_prompt`.
- The wake-word and microphone simulator nodes publish placeholder strings rather than raw audio.
- The package metadata does not declare every runtime dependency, so this README installs them explicitly.
- The repository does not include a physical robot driver or safety supervisor for `/cmd_vel`.
- Before commanding a physical robot, add command timeouts, emergency-stop handling, and velocity limits in the robot controller.

## Development notes

The main implementation files are:

```text
web/app/page.tsx                              Browser microphone client
web/bridge.js                                 WebSocket-to-TCP bridge
src/voice/voice/
  audio_receiver_node.py                      PCM receiver and faster-whisper STT
  command_parser.py                           Transcript-to-command parser
  audio_publisher.py                          Mock /audio_in publisher
  mic_publisher.py                            Local microphone simulator
  wake_word_node.py                           Wake-word bridge
  llm_node.py                                 Ollama client
  tts_node.py                                 Piper TTS client
```

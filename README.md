# Orion Humanoid Software System

This is gonna include complete software system of the humanoid ORION. Currently it has an end-to-end voice command pipeline. A browser captures microphone audio and sends 16-bit PCM audio over WebSocket to a Node.js bridge. The bridge forwards the audio over TCP to a ROS 2 receiver, which transcribes it with faster-whisper. Recognized commands are converted into ROS 2 velocity and action messages.

## Project status

- The **voice pipeline** (browser → WebSocket bridge → ROS 2 → transcripts) and the **web dashboard** work end to end. Motion outputs (`/cmd_vel`, `/robot_action`) are **disabled by default** (`ORION_ENABLE_MOTION=1` re-enables them), so nothing physical or simulated can move unless you opt in.
- The **Gazebo simulation is not yet complete.** Its launch files and keyboard walk-test node are being reworked, so the simulation steps below do not run yet. See [Gazebo simulation status](#gazebo-simulation-status).
- Everything else in this README is a complete setup guide for the project as it exists today. Follow [Setup overview](#setup-overview) to set up every component.

## Architecture

```text
Browser microphone
       |
       | WebSocket, same origin (/audio on the dashboard server)
       v
Merged dashboard + bridge server (:3000)
       |
       | TCP
       v
ROS 2 audio_receiver (:50005)
       |
       | /speech_to_text
       v
ROS 2 command_parser
       |                         |                          |
       | /cmd_vel (disabled       | /robot_action (disabled  | /llm_prompt (conversation:
       |  by default)             |  by default)             |  greetings + anything
       v                         v                          |  that is not a motion cmd)
Robot motion controller      Robot action state              v
(stopped unless              (stopped unless          ROS 2 llm_brain (Ollama)
 ORION_ENABLE_MOTION=1)       ORION_ENABLE_MOTION=1)         |
                                                             | /llm_response
                                                             v
                                                      ROS 2 tts_node (Piper)
```

## Requirements

### Operating system

- Ubuntu 24.04
- Windows WSL2 with Ubuntu is supported

### Software

- ROS 2 Jazzy
- Python 3.10 or newer
- `python3-pip` and `python3-venv`
- Node.js 20.9 or newer and npm (For web dashboard)
- Gazebo: ROS-Gazebo integration (`ros-jazzy-ros-gz`) for simulation, still in Work in progress

## Setup overview

Follow these steps in order to set up every part of the Orion project from a fresh clone:

1. [Clone the workspace](#clone-the-workspace)
2. [Install ROS 2 and Python dependencies](#install-ros-and-python-dependencies)
3. [Build the ROS 2 package](#build-the-ros-2-package)
4. [Download the TTS model](#download-the-tts-model)
5. [Install Node.js and the web application](#install-the-web-application)
6. [Run the primary voice pipeline](#run-the-primary-voice-pipeline) and [verify the pipeline](#verify-the-pipeline)

## Where everything runs

The project spans two operating systems. Placement matters more than the commands themselves.

| # | Component | Runs in | Started with |
| --- | --- | --- | --- |
| 1 | Ollama + `llama3.2:1b` | **Windows** (PowerShell) | `ollama pull llama3.2:1b`, then keep Ollama running |
| 2 | ROS 2, `colcon`, pip, Node | **WSL** (Ubuntu) | the install steps below |
| 3 | `audio_receiver` | **WSL** — Terminal 1 | `ros2 run orion_voice audio_receiver` |
| 4 | `command_parser` | **WSL** — Terminal 2 | `ros2 run orion_voice command_parser` |
| 5 | Dashboard + audio bridge (`server.js`) | **WSL** — Terminal 3 | `npm run dev` |
| 6 | Browser | Same machine (`http://localhost:3000`) or another device on the LAN (`http://<wsl-host-ip>:3000`) | allow mic, click **Start Live Microphone Stream** |

Only step 1 is Windows. Every terminal numbered below is a **WSL** terminal, not PowerShell. The browser step is the only other thing that happens on Windows, and it behaves like any ordinary web page.

## Clone the workspace

The TTS node currently expects the workspace at `~/orion` because it uses `~/orion/models/...` as a model path.

```bash
git clone https://github.com/nathanlobo/orion.git
cd ~/orion
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
python3 -m pip install --user --break-system-packages \
  faster-whisper \
  numpy \
  requests \
  sounddevice \
  piper-tts
```

Ubuntu 22.04+ marks its Python as [externally managed (PEP 668)](https://peps.python.org/pep-0668/), so plain `pip install` fails with `error: externally-managed-environment`. `--break-system-packages` is required here.

Do **not** use a virtual environment for these packages. The generated node scripts in `install/orion_voice/lib/orion_voice/` carry a fixed `#!/usr/bin/python3` shebang, so `ros2 run` always uses the system interpreter and would never see a venv's `site-packages`. Installing to the user site directory (`--user`, i.e. `~/.local/lib/python3.12/site-packages`) keeps them visible to that interpreter without touching system-owned files.

Verify the install:

```bash
python3 -c "import faster_whisper, sounddevice, numpy, requests; print('ok')"
python3 -m piper --help
```

The first start of `audio_receiver` downloads the faster-whisper `tiny.en` model. Internet access is required on that first run. To prove the model + inference work without ROS:

```bash
cd ~/orion
python3 src/voice/voice/test_whisper.py
# expect: "Inference successful! Whisper model is working properly."
```

## Build the ROS 2 package

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
colcon build --packages-select orion_voice
source install/setup.bash
```

After changing Python files, rebuild and source the workspace again:

```bash
colcon build --packages-select orion_voice
source install/setup.bash
```

## Download the TTS model

The repository ignores `models/`, so a fresh clone does not contain the Piper voice model. `tts_node` loads `~/orion/models/en_US-lessac-low.onnx` and its JSON file, which is why the workspace must live at `~/orion` (see [Clone the workspace](#clone-the-workspace)).

```bash
mkdir -p ~/orion/models
wget -O ~/orion/models/en_US-lessac-low.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/low/en_US-lessac-low.onnx
wget -O ~/orion/models/en_US-lessac-low.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/low/en_US-lessac-low.onnx.json
ls -l ~/orion/models/en_US-lessac-low.onnx*
```

Skip this step if you do not plan to run `tts_node`.

## Install the web application

### Install Node.js

The dashboard requires Node.js 20.9 or newer because of Next.js 16. The Ubuntu 24.04 `nodejs` package only provides Node.js 18, and inside WSL `npm` may resolve to a Windows installation. Install Node.js inside Ubuntu/WSL from NodeSource:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version   # must print v20.9 or newer
npm --version
```

Then install the dependencies:

```bash
cd ~/orion/web
npm install
```

The web application contains the merged dashboard + bridge server (`server.js`):

- `npm run dev`: start the dashboard and the `/audio` WebSocket bridge in one process (port `3000` by default, override with `PORT`)
- `npm run build`: create a production build
- `npm start`: serve a production build (also runs the bridge)

## Run the primary voice pipeline

Open **four to six** terminals, **all inside WSL**. You can open them with `wsl` from PowerShell, or with a VS Code window using the WSL extension — but every command below runs in Ubuntu, not PowerShell itself. In each ROS terminal, source both ROS 2 and the workspace:

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

The one Windows-side component is Ollama, covered in [Ollama setup](#ollama-setup). See [Where everything runs](#where-everything-runs) for the full placement table.

### Terminal 1 (WSL): audio receiver and speech-to-text

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
source install/setup.bash
PYTHONUNBUFFERED=1 ros2 run orion_voice audio_receiver
```

This node listens on TCP `0.0.0.0:50005`, transcribes English audio with faster-whisper (`tiny.en`, int8 on CPU), and publishes `/speech_to_text`. Speech is detected by an RMS threshold (`0.04`) with ~0.5 s of trailing silence ending an utterance; snippets shorter than 0.4 s are dropped and continuous speech is force-transcribed after 5 s.

### Terminal 2 (WSL): command parser

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run orion_voice command_parser
```

This node splits transcripts two ways. Motion phrases stay local: `walk/move/go/step forward` → `+0.3 m/s`, `walk/move/go/step back` → `-0.3 m/s`, `turn/rotate left` → `+0.5 rad/s`, `turn/rotate right` → `-0.5 rad/s`, `stop/halt/freeze/don't move` → full stop. **Everything else is conversational and goes to the LLM:** `wave/hello` sends a greeting prompt to `/llm_prompt`, and any other text is forwarded verbatim so Ollama replies on `/llm_response` for `tts_node` to speak. Nothing is ever dropped. **Motion outputs are disabled by default:** unless `ORION_ENABLE_MOTION=1` is set, the node only logs `Motion suppressed ... would have published ...` and publishes **nothing** to `/cmd_vel` or `/robot_action` (LLM forwarding always works regardless). To re-enable motion (real robot or sim actuators):

```bash
ORION_ENABLE_MOTION=1 ros2 run orion_voice command_parser
```

### Terminal 3 (WSL): dashboard + audio bridge (one process)

```bash
cd ~/orion/web
npm run dev
```

This starts a single Node process that serves the Next.js dashboard **and** the `/audio` WebSocket bridge on the same port (`3000` by default, `PORT` to change it). The browser streams mic PCM to `ws(s)://<same-host>/audio`; the server forwards each chunk over TCP to the ROS 2 receiver at `127.0.0.1:50005` (`ROS_HOST` / `ROS_PORT` to change it).

Expected behavior:

- Dashboard: `http://localhost:3000`
- Audio WebSocket: same origin, path `/audio`
- ROS TCP destination: `127.0.0.1:50005`

The bridge and `audio_receiver` are configured to run in the same WSL environment. If they run on different machines, set `ROS_HOST` and open TCP port `50005` between them.

Open the URL printed by the server, usually `http://localhost:3000`. From another device on the same LAN, use `http://<wsl-host-ip>:3000` (find it with `hostname -I` inside WSL). Grant microphone permission, then click **Start Live Microphone Stream**.

### Terminal 4 (WSL): LLM brain (Ollama) — optional, only for conversation

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run orion_voice llm_brain
```

This node subscribes to `/llm_prompt`, calls the Windows Ollama at `http://<windows-host-ip>:11434/api/generate` (gateway from `ip route show default`) with model `llama3.2:1b`, and publishes replies on `/llm_response`. It expects Ollama running on Windows with `llama3.2:1b` pulled (see [Ollama setup](#ollama-setup)). If it logs `Failed to reach Windows Ollama`, Ollama is not running on Windows or port `11434` is unreachable from WSL. Skip this terminal if you only want motion commands and no spoken replies.

### Terminal 5 (WSL): watch LLM replies as text — optional

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 topic echo /llm_response
```

Works even without speakers — useful for confirming the LLM answered before wiring up TTS. Skip if you don't need to see text replies.

### Terminal 6 (WSL): speak replies out loud — optional

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run orion_voice tts_node
```

Needs the Piper model from [Download the TTS model](#download-the-tts-model) and working WSL audio output for `paplay`. Skip this step if you only want text replies.

### Expected end-to-end flow

1. You speak into the dashboard mic while streaming → `audio_receiver` transcribes → publishes `/speech_to_text`.
2. `command_parser` reads `/speech_to_text`:
   - Motion phrases (`walk forward`, `turn left`, `stop`, …) → local motion path (silent unless `ORION_ENABLE_MOTION=1`).
   - `hello`/`wave` → greeting prompt to `/llm_prompt`.
   - Anything else (`how are you?`, `what time is it`, …) → forwarded to `/llm_prompt`.
3. `llm_brain` calls Ollama → publishes reply on `/llm_response`.
4. `tts_node` (if running) speaks the reply via Piper + `paplay`.

Test by speaking into the mic, or skip the mic entirely by injecting a transcript:

```bash
ros2 topic pub --once /speech_to_text std_msgs/msg/String "{data: 'how are you?'}"
```

Expected log chain:

- Terminal 2: `Received Speech Input: "how are you?"` → `Not a motion command, forwarding to LLM: "how are you?"`
- Terminal 4: `Thinking about: "Answer briefly ... User said: how are you?"` → `Response: ...`
- Terminal 5: prints the reply text
- Terminal 6 (if running): `Synthesizing speech for: ...` → `Speaking...`

Try `"hello"` too — Terminal 2 logs `Greeting heard: forwarding to LLM for a spoken reply` and the LLM answers with a greeting. Motion phrases never reach the LLM.

## Verify the pipeline

Inspect speech transcripts:

```bash
ros2 topic echo /speech_to_text
```

Useful checks:

```bash
ros2 topic list
ros2 node list
ss -ltn | grep -E '50005|3000'
```

### Test the full voice path (mic → transcript)

With all three terminals running, speak into the mic while streaming from the dashboard, then check the transcript in a fourth terminal:

```bash
ros2 topic echo /speech_to_text
```

Expected: your words appear as `data: '...'`. If nothing appears, check Terminal 1 (`audio_receiver`) for `>>> STT Output ... <<<` — silence below the RMS threshold (`0.04`) or snippets under 0.4 s are dropped by design.

### Test motion classification without moving anything

Motion publishing is disabled by default, but classification still logs. In a fourth terminal:

```bash
# Watch what the parser would do (publishes nothing unless ORION_ENABLE_MOTION=1)
ros2 topic echo /robot_action   # stays silent by default — expected

# Inject a fake transcript directly (bypasses mic + STT)
ros2 topic pub --once /speech_to_text std_msgs/msg/String "{data: 'turn left'}"
```

Expected in Terminal 2 (`command_parser`): `Received Speech Input: "turn left"`, then `Exec: Turning Left (0.5 rad/s)`, then `Motion suppressed (ORION_ENABLE_MOTION=0): would have published ACTION: TURNING_LEFT`. `/robot_action` stays silent and nothing moves.

### Test conversation end to end (speech → Ollama → spoken reply)

Motion commands stay local; everything else now flows to the LLM. With Terminals 1–3 running, start the conversation nodes in extra terminals (source ROS 2 + workspace in each):

```bash
# Terminal A — the LLM (needs Ollama on Windows, see Ollama setup Step 3)
ros2 run orion_voice llm_brain

# Terminal B — watch replies as text (works even without speakers)
ros2 topic echo /llm_response

# Terminal C (optional) — hear the reply spoken (needs TTS model + WSL audio)
ros2 run orion_voice tts_node
```

Then speak into the dashboard mic while streaming, or inject a transcript directly to skip the mic:

```bash
# Terminal D — fake what the STT would have heard
ros2 topic pub --once /speech_to_text std_msgs/msg/String "{data: 'how are you?'}"
```

Expected chain in the logs:

1. Terminal 2 (`command_parser`): `Received Speech Input: "how are you?"` → `Not a motion command, forwarding to LLM: "how are you?"`
2. Terminal A (`llm_brain`): `Thinking about: "Answer briefly ... User said: how are you?"` → `Response: ...`
3. Terminal B (`/llm_response` echo): prints the reply text
4. Terminal C (`tts_node`, if running): `Synthesizing speech for: ...` → `Speaking...`

Try `"hello"` too: Terminal 2 logs `Greeting heard: forwarding to LLM for a spoken reply` and the LLM answers with a greeting. Motion phrases (`walk forward`, `turn left`, `stop`) never reach the LLM — they stay on the motion path above. If Terminal A logs `Failed to reach Windows Ollama`, Ollama is not running on Windows or port `11434` is unreachable — go back to Ollama setup Step 3.

### Test the wake-word chain without speaking

In extra terminals (source ROS 2 + workspace in each):

```bash
# Terminal A — wake word listener
ros2 run orion_voice wake_word

# Terminal B — watch the prompt it emits
ros2 topic echo /llm_prompt

# Terminal C — fake a mic event (bypasses audio entirely)
ros2 topic pub --once /audio_in std_msgs/msg/String "{data: 'Hey Robot'}"
```

Expected: Terminal A logs `WAKE WORD DETECTED!`, Terminal B prints the greeting prompt. Anything without the exact case-sensitive `Hey Robot` logs `Ignoring background noise...` and publishes nothing. Chain it into the LLM test below by also running `llm_brain` (it subscribes to `/llm_prompt`).

The voice-command package classifies transcripts, but motion publishing is **disabled by default** (`ORION_ENABLE_MOTION=1` re-enables it), and nothing is connected to a physical robot controller yet. See [Gazebo simulation status](#gazebo-simulation-status).

## ROS topics

| Topic | Type | Publisher | Subscriber | Purpose |
| --- | --- | --- | --- | --- |
| `/speech_to_text` | `std_msgs/msg/String` | `audio_receiver` | `command_parser` | Whisper transcript |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | `command_parser` (only if `ORION_ENABLE_MOTION=1`) | motion controller (none connected) | Velocity command |
| `/robot_action` | `std_msgs/msg/String` | `command_parser` (only if `ORION_ENABLE_MOTION=1`) | — | Action status string |
| `/audio_in` | `std_msgs/msg/String` | `audio_simulator`, `mic_publisher` | `wake_word` | Simulated audio/wake-word input |
| `/llm_prompt` | `std_msgs/msg/String` | `wake_word`, `command_parser` | `llm_brain` | Prompt for Ollama |
| `/llm_response` | `std_msgs/msg/String` | `llm_brain` | `tts_node` | Text for speech synthesis |

The browser sends raw PCM through the TCP receiver path; it does not publish raw audio to `/audio_in`.

## Development notes

The main implementation files are:

```text
web/app/page.tsx                              Browser microphone client
web/server.js                                 Merged dashboard + WebSocket-to-TCP bridge
src/voice/voice/
  audio_receiver_node.py                      PCM receiver and faster-whisper STT
  command_parser.py                           Transcript-to-command parser
  audio_publisher.py                          Mock /audio_in publisher
  mic_publisher.py                            Local microphone simulator
  wake_word_node.py                           Wake-word bridge
  llm_node.py                                 Ollama client
  tts_node.py                                 Piper TTS client
  test_whisper.py                             Standalone faster-whisper smoke test (no ROS)
```

## Ollama setup

`llm_brain` is the only ROS node that reaches out of WSL. It discovers the Windows gateway from `ip route show default` and POSTs to `http://<windows-host-ip>:11434/api/generate`. The Ollama instance must live on Windows for this to work — WSL's `ip route` default gateway is the Windows side of the network.

**Step 1 — Windows, in PowerShell (NOT WSL):** install Ollama from [ollama.com](https://ollama.com) if it is not already installed, then pull the model this node is built for:

```powershell
ollama pull llama3.2:1b
```

This must run in Windows. Running `ollama pull` inside WSL installs a separate Linux copy that `llm_brain` can never reach.

**Step 2 — Windows:** make sure Ollama is actually running. The pull command does not keep a server alive after a reboot; you need the Ollama tray app / `ollama.exe` process up. If it is not running, restart it from the Start menu before the WSL nodes.

**Step 3 — WSL, verify the link:**

```bash
# Windows host IP as seen from WSL (used by the node automatically):
ip route show default | awk '{print $3}'

# Prove WSL can reach Windows on 11434, and that the model is listed:
curl -s http://$(ip route show default | awk '{print $3}'):11434/api/tags
```

Expected output contains `"name":"llama3.2:1b"`. If it returns `curl: (7) Failed to connect` or empty, Ollama is either not running or bound to `127.0.0.1` only. Start it from the Windows Start menu, and if it still fails, set `OLLAMA_HOST=0.0.0.0` in the Windows environment before launching Ollama.

**Step 4 — WSL:** run the nodes that use Ollama. These are the same commands as in [Run the primary voice pipeline](#run-the-primary-voice-pipeline):

- Terminal 4: `ros2 run orion_voice llm_brain` (optional — only for conversation)
- Terminal 5: `ros2 topic echo /llm_response` (optional — watch replies as text)
- Terminal 6: `ros2 run orion_voice tts_node` (optional — speak replies out loud)

Start Ollama on Windows first (Steps 1–2 above), then start the nodes in WSL with ROS 2 and the workspace sourced:

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Skip Step 4 entirely if you do not plan to use the LLM/conversation path at all.

## Gazebo simulation status

**The Gazebo simulation is not yet complete.** The simulation launch files (`voice_test_gazebo.launch.py`, `orion_walk_test.launch.py`) and the keyboard walk-test node (`voice/orion_walk_test.py`) are being reworked and are not in the repository at the moment, so the `ros2 launch` and `ros2 run orion_voice orion_walk_test` commands shown below do not run yet. The voice pipeline, dashboard, bridge, TTS, and Ollama nodes are unaffected.

### What exists today

- `src/voice/worlds/voice_test_world.sdf` — a minimal test world with a ground plane, a sun, and physics.
- `src/voice/models/voice_test_bot.sdf` — a small differential-drive test robot. It is a disposable test model, not Orion or a description of the final robot. The Gazebo DiffDrive system limits simulated speed to 0.5 m/s and turning speed to 1.0 rad/s.
- `src/voice/models/orion_walk_test.sdf` — a primitive eight-joint biped test model.
- The Gazebo dependencies `ros_gz_sim` and `ros_gz_bridge`, declared in `package.xml`.

### What is still missing

- The `voice_test_gazebo.launch.py` and `orion_walk_test.launch.py` launch files, and the `voice/orion_walk_test.py` keyboard controller.
- A ROS-Gazebo bridge from the voice pipeline's `/cmd_vel` into the simulation. Even when complete, the simulation is planned to be driven directly through Gazebo Transport first.
- Balance feedback for the biped gait. The gait is open-loop, so falling is expected; it is not a validated walking controller or a model of the final robot.

### Simulation prerequisites

Install Gazebo Harmonic and the ROS 2 Jazzy Gazebo integration if they are not already installed. Once ROS 2 is sourced, the `gz` command is on `PATH` (Gazebo Harmonic, `gz sim` 8.x):

```bash
sudo apt update
sudo apt install -y ros-jazzy-ros-gz
source /opt/ros/jazzy/setup.bash
gz sim --versions
```

### Planned workflow once the simulation is complete

```bash
cd ~/orion
source /opt/ros/jazzy/setup.bash
colcon build --packages-select orion_voice
source install/setup.bash

# Terminal 1 — Gazebo and the spawned robot (launch file not available yet)
ros2 launch orion_voice orion_walk_test.launch.py

# Terminal 2 — keyboard controller (node not available yet)
ros2 run orion_voice orion_walk_test
```

The keyboard controls are planned to be `W`/`S` for forward/backward, `A`/`D` for an experimental left/right stride bias, `Space` to stop the gait and command a neutral leg pose, and `Q` to exit the controller. Turning is not guaranteed, and falling is expected while the gait has no balance feedback.

With the simulation running, drive commands are sent through Gazebo Transport, not ROS 2:

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

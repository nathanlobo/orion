# Graph Report - orion  (2026-10-07)

## Corpus Check
- Corpus is ~4,208 words - fits in a single context window. You may not need a graph.

## Summary
- 138 nodes · 143 edges · 21 communities (14 shown, 7 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Web Dashboard Dependencies
- TypeScript Build Configuration
- Ollama and Speech Output
- Browser Audio Streaming
- Whisper Speech Recognition
- Voice Command Parsing
- Microphone Input Mock
- Web Runtime Dependencies
- Mock Audio Publisher
- Wake Word Processing
- Development Dependencies
- Copyright Test
- Flake8 Test
- Docstring Test
- Next.js Configuration
- Global Web Types and Styles
- Next Build Types
- PostCSS Configuration

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 15 edges
2. `FastAudioWhisperReceiverNode` - 10 edges
3. `CommandParserNode` - 7 edges
4. `LLMProcessor` - 7 edges
5. `MicPublisher` - 6 edges
6. `TTSProcessor` - 6 edges
7. `WakeWordProcessor` - 6 edges
8. `AudioSimulator` - 5 edges
9. `scripts` - 5 edges
10. `test_copyright()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `PCM Audio Transport` --conceptually_related_to--> `FastAudioWhisperReceiverNode`  [INFERRED]
  README.md → src/voice/voice/audio_receiver_node.py
- `Browser-to-ROS Voice Command Pipeline` --conceptually_related_to--> `FastAudioWhisperReceiverNode`  [INFERRED]
  README.md → src/voice/voice/audio_receiver_node.py
- `Rule-Based Command Mapping` --conceptually_related_to--> `CommandParserNode`  [INFERRED]
  README.md → src/voice/voice/command_parser.py
- `External Robot Motion Controller` --conceptually_related_to--> `CommandParserNode`  [INFERRED]
  README.md → src/voice/voice/command_parser.py
- `Local LLM and Spoken Response` --conceptually_related_to--> `WakeWordProcessor`  [INFERRED]
  README.md → src/voice/voice/wake_word_node.py

## Import Cycles
- None detected.

## Communities (21 total, 7 thin omitted)

### Community 0 - "Web Dashboard Dependencies"
Cohesion: 0.11
Nodes (17): next, react-dom, tailwindcss, @tailwindcss/postcss, @types/node, @types/react, @types/react-dom, @types/ws (+9 more)

### Community 1 - "TypeScript Build Configuration"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+9 more)

### Community 2 - "Ollama and Speech Output"
Cohesion: 0.18
Nodes (7): Local LLM and Spoken Response, LLMProcessor, main(), Node, main(), Node, TTSProcessor

### Community 3 - "Browser Audio Streaming"
Cohesion: 0.15
Nodes (9): PCM Audio Transport, Browser-to-ROS Voice Command Pipeline, react, ws, metadata, AudioDashboard(), net, { WebSocketServer } (+1 more)

### Community 4 - "Whisper Speech Recognition"
Cohesion: 0.29
Nodes (4): Local Speech Recognition, FastAudioWhisperReceiverNode, main(), Node

### Community 5 - "Voice Command Parsing"
Cohesion: 0.29
Nodes (5): Rule-Based Command Mapping, External Robot Motion Controller, CommandParserNode, main(), Node

### Community 6 - "Microphone Input Mock"
Cohesion: 0.33
Nodes (3): main(), MicPublisher, Node

### Community 7 - "Web Runtime Dependencies"
Cohesion: 0.29
Nodes (7): dependencies, next, react, react-dom, tailwindcss, @tailwindcss/postcss, ws

### Community 8 - "Mock Audio Publisher"
Cohesion: 0.40
Nodes (3): AudioSimulator, main(), Node

### Community 9 - "Wake Word Processing"
Cohesion: 0.40
Nodes (3): main(), Node, WakeWordProcessor

### Community 10 - "Development Dependencies"
Cohesion: 0.33
Nodes (6): devDependencies, @types/node, @types/react, @types/react-dom, @types/ws, typescript

### Community 11 - "Copyright Test"
Cohesion: 0.40
Nodes (4): copyright, skip, linter, test_copyright()

### Community 12 - "Flake8 Test"
Cohesion: 0.50
Nodes (3): flake8, linter, test_flake8()

### Community 13 - "Docstring Test"
Cohesion: 0.50
Nodes (3): pep257, linter, test_pep257()

## Knowledge Gaps
- **53 isolated node(s):** `*.css`, `metadata`, `{ WebSocketServer }`, `net`, `wss` (+48 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 85 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ws` connect `Browser Audio Streaming` to `Web Dashboard Dependencies`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `FastAudioWhisperReceiverNode` connect `Whisper Speech Recognition` to `Browser Audio Streaming`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `dependencies` connect `Web Runtime Dependencies` to `Web Dashboard Dependencies`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `FastAudioWhisperReceiverNode` (e.g. with `PCM Audio Transport` and `Browser-to-ROS Voice Command Pipeline`) actually correct?**
  _`FastAudioWhisperReceiverNode` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `CommandParserNode` (e.g. with `Rule-Based Command Mapping` and `External Robot Motion Controller`) actually correct?**
  _`CommandParserNode` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `*.css`, `metadata`, `{ WebSocketServer }` to the rest of the system?**
  _53 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Web Dashboard Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
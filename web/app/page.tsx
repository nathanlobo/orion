'use client';

import { useState, useRef } from 'react';

export default function AudioDashboard() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamingRef = useRef(false);

  const getBridgeUrl = () => {
    const { host, protocol } = window.location;
    const wsProtocol = protocol === 'https:' ? 'wss' : 'ws';
    return `${wsProtocol}://${host}/audio`;
  };

  const cleanupAudio = () => {
    try {
      processorRef.current?.disconnect();
    } catch { /* ignore */ }
    try {
      sourceRef.current?.disconnect();
    } catch { /* ignore */ }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    processorRef.current = null;
    sourceRef.current = null;
    audioCtxRef.current = null;
    streamRef.current = null;
  };

  const startStreaming = async () => {
    if (isStreaming || isConnecting) return;
    setErrorMessage(null);
    setIsConnecting(true);

    let stream: MediaStream;
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('Microphone access requires HTTPS or localhost.');
      }
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      const message =
        err instanceof DOMException && err.name === 'NotAllowedError'
          ? 'Microphone permission was denied.'
          : err instanceof DOMException && err.name === 'NotFoundError'
            ? 'No microphone found. Check input device.'
            : err instanceof Error ? err.message : 'Unable to access mic.';
      setErrorMessage(message);
      setIsConnecting(false);
      return;
    }
    streamRef.current = stream;

    const bridgeUrl = getBridgeUrl();
    let ws: WebSocket;
    try {
      ws = new WebSocket(bridgeUrl);
    } catch (err) {
      cleanupAudio();
      setErrorMessage('Unable to connect to ' + bridgeUrl);
      console.error(err);
      setIsConnecting(false);
      return;
    }
    wsRef.current = ws;
    ws.binaryType = 'arraybuffer';
    ws.onerror = () => console.error('Bridge socket error');
    ws.onclose = () => {
      if (!streamingRef.current) {
        cleanupAudio();
        wsRef.current = null;
        setErrorMessage('Cannot reach the audio bridge. Is the server running?');
        setIsConnecting(false);
      } else {
        stopStreaming();
        setErrorMessage('Lost connection to the audio bridge.');
      }
    };
    ws.onopen = async () => {
      try {
        const AC = window.AudioContext;
        const audioCtx = new AC({ sampleRate: 16000 });
        audioCtxRef.current = audioCtx;
        if (audioCtx.state === 'suspended') await audioCtx.resume();
        const source = audioCtx.createMediaStreamSource(streamRef.current!);
        sourceRef.current = source;
        const processor = audioCtx.createScriptProcessor(2048, 1, 1);
        processorRef.current = processor;
        processor.onaudioprocess = (e) => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0);
            const pcmData = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
              pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7fff;
            }
            wsRef.current.send(pcmData.buffer);
          }
        };
        source.connect(processor);
        processor.connect(audioCtx.destination);
        streamingRef.current = true;
        setIsStreaming(true);
        setIsConnecting(false);
      } catch (err) {
        cleanupAudio();
        try { ws.close(); } catch { /* ignore */ }
        wsRef.current = null;
        setErrorMessage(err instanceof Error ? err.message : 'Unable to start streaming.');
        setIsConnecting(false);
      }
    };
  };

  const stopStreaming = () => {
    cleanupAudio();
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      try { wsRef.current.close(); } catch { /* ignore */ }
    }
    wsRef.current = null;
    streamingRef.current = false;
    setIsStreaming(false);
    setIsConnecting(false);
  };

  return (
    <main className="dashboard">
      <h1 className="dashboard-title">Orion Command Center</h1>
      <p className="dashboard-status">
        Status: {isConnecting ? <span className="status-live">Connecting…</span> : isStreaming ? <span className="status-live">Streaming Microphone Live</span> : <span className="status-idle">Idle</span>}
      </p>
      {errorMessage && <p className="dashboard-error">{errorMessage}</p>}

      <button
        onClick={isStreaming ? stopStreaming : startStreaming}
        disabled={isConnecting}
        className={`microphone-button ${isStreaming ? 'stop' : 'start'}`}
      >
        {isConnecting ? 'Connecting…' : isStreaming ? 'Stop Microphone' : 'Start Live Microphone Stream'}
      </button>
    </main>
  );
}
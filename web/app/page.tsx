'use client';

import { useState, useRef } from 'react';

export default function AudioDashboard() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  const startStreaming = async () => {
    setErrorMessage(null);

    try {
      const host = window.location.hostname;
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket('wss://bridge.codinx.app');
      wsRef.current = ws;

      ws.onopen = async () => {
        try {
          if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error('Microphone access requires a secure browser context.');
          }

          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          streamRef.current = stream;
          const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
          audioCtxRef.current = audioCtx;

          const source = audioCtx.createMediaStreamSource(stream);
          const processor = audioCtx.createScriptProcessor(2048, 1, 1);
          processorRef.current = processor;

          processor.onaudioprocess = (e) => {
            if (ws.readyState === WebSocket.OPEN) {
              const inputData = e.inputBuffer.getChannelData(0);
              const pcmData = new Int16Array(inputData.length);
              for (let i = 0; i < inputData.length; i++) {
                pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7fff;
              }
              ws.send(pcmData.buffer);
            }
          }

          source.connect(processor);
          processor.connect(audioCtx.destination);
          setIsStreaming(true);
        } catch (err) {
          streamRef.current?.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
          ws.close();
          const message = err instanceof DOMException && err.name === 'NotAllowedError'
            ? 'Microphone permission was denied by the browser or operating system.'
            : err instanceof Error ? err.message : 'Unable to start microphone streaming.';
          setErrorMessage(message);
          console.error('Unable to start microphone streaming:', err);
        }
      };
    } catch (err) {
      setErrorMessage('Unable to connect to the audio bridge.');
      console.error('Unable to connect to the audio bridge:', err);
    }
  };

  const stopStreaming = () => {
    if (processorRef.current) processorRef.current.disconnect();
    if (audioCtxRef.current) audioCtxRef.current.close();
    if (streamRef.current) streamRef.current.getTracks().forEach((track) => track.stop());
    if (wsRef.current) wsRef.current.close();
    processorRef.current = null;
    audioCtxRef.current = null;
    streamRef.current = null;
    wsRef.current = null;
    setIsStreaming(false);
  };

  return (
    <main className="dashboard">
      <h1 className="dashboard-title">Humanoid Command Center</h1>
      <p className="dashboard-status">
        Status: {isStreaming ? <span className="status-live">🟢 Streaming Microphone Live</span> : <span className="status-idle">🔴 Idle</span>}
      </p>
      {errorMessage && <p className="dashboard-error">{errorMessage}</p>}

      <button
        onClick={isStreaming ? stopStreaming : startStreaming}
        className={`microphone-button ${isStreaming ? 'stop' : 'start'}`}
      >
        {isStreaming ? 'Stop Microphone' : 'Start Live Microphone Stream'}
      </button>
    </main>
  );
}
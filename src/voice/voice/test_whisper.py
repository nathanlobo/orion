import numpy as np
from faster_whisper import WhisperModel

print("Loading model...")
model = WhisperModel("tiny.en", device="cpu", compute_type="int8")

# Generate 2 seconds of silence/dummy float32 audio
dummy_audio = np.zeros(16000 * 2, dtype=np.float32)

print("Running test inference...")
segments, info = model.transcribe(dummy_audio, beam_size=1)
print("Inference successful! Whisper model is working properly.")
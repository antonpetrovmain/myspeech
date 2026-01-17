import io
import wave
import threading
import time
import numpy as np
import sounddevice as sd

import config


class Recorder:
    def __init__(self):
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._recording = False

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        with self._lock:
            if self._recording:
                self._frames.append(indata.copy())

    def start(self):
        # Ensure any previous stream is closed
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
            time.sleep(0.1)  # Let audio subsystem settle

        with self._lock:
            self._frames = []
            self._recording = True

        try:
            device = config.AUDIO_DEVICE
            self._stream = sd.InputStream(
                samplerate=config.SAMPLE_RATE,
                channels=config.CHANNELS,
                dtype=np.int16,
                device=device,
                callback=self._audio_callback,
            )
            self._stream.start()
        except Exception:
            with self._lock:
                self._recording = False

    def stop(self) -> bytes:
        with self._lock:
            self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._frames:
                return b""
            audio_data = np.concatenate(self._frames, axis=0)

        # Check minimum duration (0.5 seconds)
        duration = len(audio_data) / config.SAMPLE_RATE
        audio_level = np.abs(audio_data).mean()

        # Convert to WAV bytes
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(config.CHANNELS)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(config.SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())

        wav_bytes = buffer.getvalue()

        # Save recording to file (before level check, so we can review failed recordings)
        if getattr(config, 'SAVE_RECORDING', False):
            with open("/tmp/myspeech_recording.wav", "wb") as f:
                f.write(wav_bytes)

        # Skip if too short or silent
        if duration < 0.5:
            return b""

        if audio_level < 100:
            return b""

        return wav_bytes

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

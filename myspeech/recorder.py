import io
import logging
import wave
import threading
import numpy as np
import sounddevice as sd

import config

log = logging.getLogger(__name__)


def get_input_devices() -> list[tuple[int, str]]:
    """Get list of available audio input devices as (index, name) tuples."""
    devices = sd.query_devices()
    return [
        (i, d['name'])
        for i, d in enumerate(devices)
        if d['max_input_channels'] > 0
    ]


def get_default_input_device() -> int:
    """Get the default input device index."""
    return sd.default.device[0]


class Recorder:
    def __init__(self):
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._recording = False
        self._device = config.AUDIO_DEVICE  # None means default
        self._stream_active = False

    def set_device(self, device_index: int | None):
        """Set the audio input device. None means use default."""
        self._device = device_index
        # Restart stream with new device if it was running
        if self._stream_active:
            self._close_stream()
            self._open_stream()

    def get_device(self) -> int | None:
        """Get the current audio input device index. None means default."""
        return self._device

    def _open_stream(self):
        """Open and start the audio input stream."""
        if self._stream:
            return  # Already open

        if self._device is not None:
            device_info = sd.query_devices(self._device)
            device_name = f"[{self._device}] {device_info['name']}"
        else:
            default_idx = sd.default.device[0]
            device_info = sd.query_devices(default_idx)
            device_name = f"Default ([{default_idx}] {device_info['name']})"

        log.info(f"Opening audio stream (device={device_name}, rate={config.SAMPLE_RATE})")
        self._stream = sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            dtype=np.int16,
            device=self._device,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._stream_active = True
        log.info("Audio stream started successfully")

    def _close_stream(self):
        """Close the audio stream."""
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
            self._stream_active = False

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        with self._lock:
            if self._recording:
                self._frames.append(indata.copy())

    def ensure_stream(self):
        """Ensure the audio stream is open. Call this at app startup for instant recording."""
        if not self._stream_active:
            try:
                self._open_stream()
            except Exception as e:
                log.warning(f"Failed to open audio stream: {e}")
                log.info("Reinitializing PortAudio and retrying...")
                try:
                    sd._terminate()
                    sd._initialize()
                    self._open_stream()
                except Exception as e2:
                    log.error(f"Failed to open audio stream after reinit: {e2}")

    def start(self):
        """Start recording. Stream is opened on first call and kept running."""
        # Ensure stream is running (instant if already open)
        self.ensure_stream()

        with self._lock:
            self._frames = []
            self._recording = True
        log.info("Recording started")

    def stop(self) -> bytes:
        """Stop recording, close the audio stream, and return audio data."""
        with self._lock:
            self._recording = False
            frames = self._frames
            self._frames = []

        log.info(f"Recording stopped, captured {len(frames)} frames")
        self._close_stream()

        if not frames:
            return b""

        audio_data = np.concatenate(frames, axis=0)

        # Apply gain if configured (boost quiet microphones)
        if config.AUDIO_GAIN != 1.0:
            # Convert to float, apply gain, clip to int16 range, convert back
            audio_float = audio_data.astype(np.float32) * config.AUDIO_GAIN
            audio_data = np.clip(audio_float, -32768, 32767).astype(np.int16)
            log.info(f"Applied gain: {config.AUDIO_GAIN}x")

        # Check minimum duration (0.5 seconds)
        duration = len(audio_data) / config.SAMPLE_RATE
        audio_level = np.abs(audio_data).mean()
        log.info(f"Recording: duration={duration:.2f}s, level={audio_level:.0f}")

        # Convert to WAV bytes
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(config.CHANNELS)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(config.SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())

        wav_bytes = buffer.getvalue()

        # Save recording to file (before level check, so we can review failed recordings)
        if config.SAVE_RECORDING:
            with open(config.RECORDING_PATH, "wb") as f:
                f.write(wav_bytes)

        # Skip if too short or silent
        if duration < config.MIN_RECORDING_DURATION:
            return b""

        if audio_level < config.MIN_AUDIO_LEVEL:
            return b""

        return wav_bytes

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

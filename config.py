# MySpeech Configuration
# Values are loaded from ~/.config/myspeech/config.toml (created on first run)

from myspeech.user_config import get

# Server (mlx-audio)
MLX_AUDIO_SERVER_URL = get("server", "url", "http://localhost:8000/v1")
WHISPER_MODEL = get("server", "model", "mlx-community/whisper-large-v3-turbo")

# Audio
SAMPLE_RATE = get("audio", "sample_rate", 16000)
CHANNELS = get("audio", "channels", 1)
_device = get("audio", "device", "default")
AUDIO_DEVICE = None if _device == "default" else _device
SAVE_RECORDING = get("audio", "save_recording", True)
RECORDING_PATH = get("audio", "recording_path", "/tmp/myspeech_recording.wav")
MIN_RECORDING_DURATION = get("audio", "min_duration", 0.5)
MIN_AUDIO_LEVEL = get("audio", "min_level", 100)

# Hotkey configuration
HOTKEY_MODIFIERS = get("hotkey", "modifiers", "cmd+ctrl")
HOTKEY_KEY = get("hotkey", "record_key", "t")
HOTKEY_OPEN_RECORDING_KEY = get("hotkey", "open_recording_key", "r")
HOTKEY_DEBOUNCE_SECONDS = get("hotkey", "debounce_seconds", 0.5)

# Popup (recording dot indicator)
POPUP_DOT_SIZE = get("popup", "dot_size", 16)
POPUP_DOT_COLOR = get("popup", "dot_color", "#ffcc00")
POPUP_DOT_ALPHA = get("popup", "dot_alpha", 0.7)

# Clipboard
PASTE_DELAY = get("clipboard", "paste_delay", 0.1)
RESTORE_CLIPBOARD = get("clipboard", "restore_clipboard", True)
RESTORE_DELAY = get("clipboard", "restore_delay", 0.2)

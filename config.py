# MySpeech Configuration

# Server (mlx-audio)
MLX_AUDIO_SERVER_URL = "http://localhost:8000/v1"

# Whisper model for transcription
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_DEVICE = None  # Set to device index (e.g., 4) or name, or None for default
SAVE_RECORDING = True  # Save last recording for playback
RECORDING_PATH = "/tmp/myspeech_recording.wav"
MIN_RECORDING_DURATION = 0.5  # Minimum seconds to accept recording
MIN_AUDIO_LEVEL = 100  # Minimum audio level to accept (prevents silent recordings)

# Hotkey (key codes detected on this system)
HOTKEY_MODIFIERS = {'cmd', 'ctrl'}
HOTKEY_KEY_CODE = 3  # T key (Cmd+Ctrl+T)
HOTKEY_OPEN_RECORDING_KEY_CODE = 1  # R key (Cmd+Ctrl+R)
HOTKEY_DEBOUNCE_SECONDS = 0.5  # Ignore new recordings within this time

# Popup (recording dot indicator)
POPUP_DOT_SIZE = 16
POPUP_DOT_COLOR = "#ffcc00"
POPUP_DOT_ALPHA = 0.7

# Clipboard
PASTE_DELAY = 0.1  # seconds to wait before pasting

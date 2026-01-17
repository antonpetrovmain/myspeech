# MySpeech Configuration

# Server (mlx-audio)
MLX_AUDIO_SERVER_URL = "http://localhost:8000/v1"

# Whisper model for transcription
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_DEVICE = None  # Set to device index (e.g., 4) or name, or None for default
SAVE_RECORDING = True  # Save last recording to /tmp/myspeech_recording.wav

# Hotkey (key codes detected on this system)
HOTKEY_MODIFIERS = {'cmd', 'ctrl'}
HOTKEY_KEY_CODE = 3  # T key (Cmd+Ctrl+T)
HOTKEY_OPEN_RECORDING_KEY_CODE = 1  # R key (Cmd+Ctrl+R)

# Popup
POPUP_WIDTH = 120
POPUP_HEIGHT = 40
POPUP_BG_COLOR = "#cc0000"
POPUP_TEXT_COLOR = "white"
POPUP_TEXT = "Recording..."
POPUP_DELAY_MS = 500  # Delay before showing popup (recording starts immediately)

# Clipboard
PASTE_DELAY = 0.1  # seconds to wait before pasting
RESTORE_DELAY = 0.2  # seconds to wait before restoring clipboard

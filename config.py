# MySpeech Configuration

# Server
MLX_SERVER_URL = "http://localhost:10240/v1"

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_DEVICE = None  # Set to device index (e.g., 4) or name, or None for default
DEBUG_SAVE_AUDIO = True  # Save recordings to /tmp/myspeech_recording.wav for debugging

# Hotkey
HOTKEY_MODIFIERS = {'cmd', 'ctrl'}
HOTKEY_CHAR = 'f'

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

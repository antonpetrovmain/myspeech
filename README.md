# MySpeech

A macOS speech-to-text application using [mlx-omni-server](https://github.com/madroidmaq/mlx-omni-server) on Apple Silicon. Hold a global hotkey to record your voice, release to transcribe and auto-paste the text.

## Features

- **Global Hotkey**: Hold Cmd+Ctrl+T to record, release to transcribe
- **Auto-paste**: Transcription is automatically pasted into your active application
- **Local Processing**: Uses Whisper via mlx-omni-server (no cloud API needed)
- **Auto-start Server**: Automatically starts mlx-omni-server if not running
- **Visual Feedback**: Red popup indicates when recording is active

## Requirements

- macOS on Apple Silicon (M1/M2/M3)
- Python 3.12 or 3.13
- Rust compiler (for building dependencies)

## Installation

### 1. Install Rust (if not already installed)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

### 2. Install tkinter (if not already installed)

```bash
brew install python-tk@3.13  # or python-tk@3.12
```

### 3. Clone and install MySpeech

```bash
git clone <repository-url>
cd myspeech

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### 4. Grant macOS Permissions

Go to **System Settings > Privacy & Security** and enable:

1. **Accessibility**: Add your terminal app (e.g., Terminal, iTerm2, WezTerm)
   - Required for global hotkey detection
2. **Microphone**: Add your terminal app
   - Required for audio recording

## Usage

### Start the application

```bash
source .venv/bin/activate
python main.py
```

### Record and transcribe

1. Press and hold **Cmd+Ctrl+T**
2. Wait for the red "Recording..." popup to appear (indicates recording is active)
3. Speak your text
4. Release the keys
5. The transcription will be automatically pasted into your active application

### Stop the application

Press **Ctrl+C** in the terminal.

## Configuration

Edit `config.py` to customize:

```python
# Server
MLX_SERVER_URL = "http://localhost:10240/v1"

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_DEVICE = None  # Set to device index or None for default

# Hotkey (uses detected character, not physical key)
HOTKEY_MODIFIERS = {'cmd', 'ctrl'}
HOTKEY_CHAR = 'f'  # The character detected when pressing your hotkey

# Popup
POPUP_WIDTH = 120
POPUP_HEIGHT = 40
POPUP_BG_COLOR = "#cc0000"
POPUP_TEXT_COLOR = "white"
POPUP_TEXT = "Recording..."
POPUP_DELAY_MS = 500  # Delay before showing popup

# Debug
DEBUG_SAVE_AUDIO = False  # Save recordings to /tmp/myspeech_recording.wav
```

### Keyboard Layout Note

If you use a non-QWERTY layout (e.g., Colemak, Dvorak), the `HOTKEY_CHAR` should be set to the character that your system reports when pressing your desired key with Cmd+Ctrl held. Run the app with debug output to see what character is detected.

### Selecting Audio Input Device

On startup, the app shows available input devices:

```
Available input devices:
  [0] MacBook Pro Microphone (DEFAULT)
  [1] External Microphone
```

Set `AUDIO_DEVICE` in config.py to the device index you want to use.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│  mlx-omni-server│    │   myspeech app  │
│  (background)   │    │                 │
│                 │    │  ┌───────────┐  │
│  /v1/audio/     │◄───┤  │transcriber│  │
│  transcriptions │    │  └───────────┘  │
│                 │    │  ┌───────────┐  │
└─────────────────┘    │  │  hotkey   │  │
                       │  └───────────┘  │
                       │  ┌───────────┐  │
                       │  │  recorder │  │
                       │  └───────────┘  │
                       │  ┌───────────┐  │
                       │  │ clipboard │  │
                       │  └───────────┘  │
                       │  ┌───────────┐  │
                       │  │   popup   │  │
                       │  └───────────┘  │
                       └─────────────────┘
```

## Troubleshooting

### "No module named '_tkinter'"

Install tkinter via Homebrew:
```bash
brew install python-tk@3.13
```

### Recording shows "Audio level too low (silence)"

- Check that the correct audio input device is selected
- Verify microphone permissions in System Settings
- Try setting `AUDIO_DEVICE` to a specific device index in config.py
- Set `DEBUG_SAVE_AUDIO = True` and check `/tmp/myspeech_recording.wav`

### Hotkey not detected

- Ensure Accessibility permission is granted for your terminal app
- If using a non-QWERTY layout, check what character is detected and update `HOTKEY_CHAR`

### Transcription returns "Thank you" or wrong text

This happens when audio is too short, too quiet, or mostly silence. Whisper may hallucinate common phrases. Ensure your microphone is working and speak clearly.

### mlx-omni-server fails to start

- Ensure you have enough disk space for model downloads
- First run downloads the Whisper model (~3GB)
- Check that port 10240 is not in use

## License

MIT

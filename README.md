# MySpeech

A macOS speech-to-text application using [mlx-audio](https://github.com/Blaizzy/mlx-audio) on Apple Silicon. Hold a global hotkey to record your voice, release to transcribe and auto-paste the text.

## Features

- **Global Hotkey**: Hold Cmd+Ctrl+T to record, release to transcribe
- **Auto-paste**: Transcription is automatically pasted into your active application
- **Playback**: Press Cmd+Ctrl+R to open and replay your last recording
- **Local Processing**: Uses Whisper via mlx-audio (no cloud API needed)
- **Auto-start Server**: Automatically starts mlx-audio server if not running
- **Visual Feedback**: Red popup indicates when recording is active

## Requirements

- macOS on Apple Silicon (M1/M2/M3/M4)
- Python 3.12+

## Installation

### 1. Install tkinter

```bash
brew install python-tk@3.13  # or python-tk@3.12
```

### 2. Clone and install

```bash
git clone https://github.com/antonpetrovmain/myspeech.git
cd myspeech

# Create virtual environment and install
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Grant macOS Permissions

Go to **System Settings > Privacy & Security** and enable:

1. **Accessibility**: Add your terminal app (Terminal, iTerm2, WezTerm, etc.)
2. **Microphone**: Add your terminal app

## Usage

```bash
source .venv/bin/activate
python main.py
```

- **Cmd+Ctrl+T** (hold): Record and transcribe
- **Cmd+Ctrl+R**: Open last recording in default audio player
- **Ctrl+C**: Quit

## Configuration

Edit `config.py` to customize settings:

```python
# Server
MLX_AUDIO_SERVER_URL = "http://localhost:8000/v1"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

# Audio
AUDIO_DEVICE = None  # Set to device index or None for default

# Hotkey (virtual key codes)
HOTKEY_MODIFIERS = {'cmd', 'ctrl'}
HOTKEY_KEY_CODE = 3  # T key

# Recording
SAVE_RECORDING = True  # Save last recording for playback with Cmd+Ctrl+R
```

## Troubleshooting

### "No module named '_tkinter'"
```bash
brew install python-tk@3.13
```

### Recording shows "Audio level too low"
- Check microphone permissions in System Settings
- Set `AUDIO_DEVICE` to a specific device index in config.py
- Use Cmd+Ctrl+R to listen to the saved recording

### Hotkey not detected
- Ensure Accessibility permission is granted for your terminal app

### Transcription returns wrong text
- Audio may be too short or quiet - Whisper can hallucinate on silence
- Ensure microphone is working and speak clearly

### Server fails to start
- First run downloads the Whisper model (~1.5GB)
- Check that port 8000 is not in use

## License

MIT

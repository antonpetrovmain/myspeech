# MySpeech

A macOS speech-to-text application using [mlx-audio](https://github.com/Blaizzy/mlx-audio) on Apple Silicon. Hold a global hotkey to record your voice, release to transcribe and auto-paste the text.

## Features

- **Global Hotkey**: Hold Cmd+Ctrl+T to record, release to transcribe
- **Auto-paste**: Transcription is automatically pasted into your active application
- **Menu Bar Icon**: Shows app status with quick access to logs and quit
- **Playback**: Press Cmd+Ctrl+R to open and replay your last recording
- **Local Processing**: Uses Whisper via mlx-audio (no cloud API needed)
- **Auto-start Server**: Automatically starts mlx-audio server if not running
- **Visual Feedback**: Yellow dot indicator when recording is active

## Requirements

- macOS 13+ on Apple Silicon (M1/M2/M3/M4)
- **MLX Audio Server** (provides the Whisper transcription backend)

### Installing MLX Audio Server

MySpeech requires the mlx-audio server running locally. Install it once:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a dedicated environment and install mlx-audio
uv venv ~/.mlx-audio-venv
source ~/.mlx-audio-venv/bin/activate
uv pip install mlx-audio

# Start the server (first run downloads ~1.5GB Whisper model)
mlx_audio.server --port 8000
```

**Tip**: Keep the server running in a terminal tab or add it to your shell startup.

## Installation

### Option 1: Pre-built macOS App (Recommended)

The easiest way to use MySpeech:

1. Download `MySpeech.app` from the latest release or [build it yourself](#building-the-app)
2. Copy to Applications folder:
   ```bash
   cp -r MySpeech.app /Applications/
   ```
3. Launch from Applications and grant permissions (see below)

### Option 2: Development Setup

For development or if you want to run from source:

1. **Install tkinter**
   ```bash
   brew install python-tk@3.13  # or python-tk@3.12
   ```

2. **Clone and install**
   ```bash
   git clone https://github.com/antonpetrovmain/myspeech.git
   cd myspeech

   # Create virtual environment with uv
   uv venv .venv
   source .venv/bin/activate
   uv pip install -e .
   ```

3. **Run the app**
   ```bash
   python main.py
   ```

### macOS Permissions

Go to **System Settings > Privacy & Security** and enable:

1. **Accessibility**: Add MySpeech.app (or your terminal app if running from source)
2. **Microphone**: Add MySpeech.app (or your terminal app)

## Usage

- **Cmd+Ctrl+T** (hold): Record and transcribe
- **Cmd+Ctrl+R**: Open last recording in default audio player
- **Menu Bar**: Click the icon for quick access to logs, last recording, and quit
- **Logs**: `~/Library/Logs/MySpeech.log`

## Building the App

To create your own `MySpeech.app`:

```bash
# Setup
uv venv .venv
source .venv/bin/activate
uv pip install -e .
uv pip install pyinstaller

# Build
pyinstaller MySpeech.spec --clean

# Result: dist/MySpeech.app
cp -r dist/MySpeech.app /Applications/
```

## Configuration

Edit `config.py` to customize:

```python
# Server
MLX_AUDIO_SERVER_URL = "http://localhost:8000/v1"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

# Audio
AUDIO_DEVICE = None  # Set to device index or None for default
MIN_RECORDING_DURATION = 0.5  # Minimum seconds to accept
MIN_AUDIO_LEVEL = 100  # Minimum audio level threshold

# Hotkey
HOTKEY_MODIFIERS = {'cmd', 'ctrl'}
HOTKEY_KEY_CODE = 3  # T key
HOTKEY_DEBOUNCE_SECONDS = 0.5  # Ignore new recordings within this time

# Recording
SAVE_RECORDING = True  # Save last recording to /tmp/myspeech_recording.wav
```

## Troubleshooting

### Hotkey not working
- Grant **Accessibility** permission: System Settings > Privacy & Security > Accessibility > Add MySpeech.app
- Check logs: `tail -f ~/Library/Logs/MySpeech.log`

### No recording captured
- Grant **Microphone** permission in System Settings
- Check audio input device: `python -c "import sounddevice; print(sounddevice.query_devices())"`
- Adjust `MIN_AUDIO_LEVEL` in config.py if microphone is quiet

### Transcription shows wrong text
- Audio may be too short or quiet - Whisper can hallucinate on silence
- Speak clearly and close to microphone
- Check `MIN_RECORDING_DURATION` and `MIN_AUDIO_LEVEL` in config.py

### "Read-only file system" error on app launch
- This is fixed in the latest version. Rebuild with: `pyinstaller MySpeech.spec --clean -y`

### "MLX Audio Server not found" dialog
- Install mlx-audio server first (see [Requirements](#installing-mlx-audio-server))
- Ensure the server is running: `mlx_audio.server --port 8000`

### Server fails to start
- First run downloads the Whisper model (~1.5GB) - wait 2-3 minutes
- Check server logs: `tail -f ~/Library/Logs/MySpeech-server.log`
- Verify port 8000 is not in use: `lsof -i :8000`
- Start manually: `source ~/.mlx-audio-venv/bin/activate && mlx_audio.server --port 8000`

### "No module named '_tkinter'" (development only)
```bash
brew install python-tk@3.13
```

## License

MIT

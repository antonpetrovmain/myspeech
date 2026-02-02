# MySpeech

A macOS speech-to-text application using [mlx-audio](https://github.com/Blaizzy/mlx-audio) on Apple Silicon. Hold a global hotkey to record your voice, release to transcribe and auto-paste the text.

## Features

- **Global Hotkey**: Hold Cmd+Ctrl+T to record, release to transcribe
- **Auto-paste**: Transcription is automatically pasted into your active application
- **Clipboard Restore**: After pasting, your original clipboard is restored (transcription stays in clipboard history)
- **Menu Bar Icon**: Shows app status with quick access to logs, settings, and audio device selection
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

# Create a dedicated environment with Python 3.12 and install mlx-audio
uv venv ~/.mlx-audio-venv --python 3.12
source ~/.mlx-audio-venv/bin/activate
uv pip install mlx-audio

# Start the server (first run downloads ~1.5GB Whisper model)
mlx_audio.server --port 8000
```

**Tip**: Keep the server running in a terminal tab or add it to your shell startup.

## Installation

### Quick Install (Recommended)

Run this one-liner in Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/antonpetrovmain/myspeech/main/install.sh | bash
```

To install to a custom directory (no admin password needed):

```bash
curl -fsSL https://raw.githubusercontent.com/antonpetrovmain/myspeech/main/install.sh | bash -s -- --dir ~/tools
```

This downloads, installs, and removes the Gatekeeper quarantine automatically. When installing to `/Applications` (default), you may be prompted for your admin password.

### Manual Install

1. Download `MySpeech-vX.X.X-macos-arm64.zip` from the [latest release](https://github.com/antonpetrovmain/myspeech/releases)
2. Extract and install (requires admin privileges):
   ```bash
   unzip MySpeech-*.zip
   sudo mv MySpeech.app /Applications/
   sudo xattr -cr /Applications/MySpeech.app
   ```
3. Launch from Applications and grant permissions (see below)

### Development Setup

For development or running from source:

```bash
git clone https://github.com/antonpetrovmain/myspeech.git
cd myspeech

# Create virtual environment with uv
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# Run the app
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

Settings are stored in `~/.config/myspeech/config.toml` (created on first run).

**To edit:** Click the menu bar icon → "Edit Settings..." or open the file directly.

```toml
[server]
url = "http://localhost:8000/v1"
model = "mlx-community/whisper-large-v3-turbo"

[audio]
device = "default"              # "default" or device index (e.g., 4)
save_recording = true
recording_path = "/tmp/myspeech_recording.wav"
min_duration = 0.5              # Minimum seconds to accept recording
min_level = 100                 # Minimum audio level (prevents silent recordings)

[hotkey]
modifiers = "cmd+ctrl"          # Modifiers: cmd, ctrl, alt, shift (separated by +)
record_key = "t"                # Hold to record (Cmd+Ctrl+T)
open_recording_key = "r"        # Open last recording (Cmd+Ctrl+R)
debounce_seconds = 0.5

[popup]
dot_size = 16
dot_color = "#ffcc00"
dot_alpha = 0.7

[clipboard]
paste_delay = 0.1               # Seconds to wait for app to activate before pasting
restore_clipboard = true        # Restore original clipboard after pasting transcription
restore_delay = 1.1             # Seconds before restoring (lets clipboard history capture transcription)
```

**Clipboard Restore:** When enabled (default), your original clipboard content is restored after pasting the transcription. The transcription remains accessible via clipboard history apps (e.g., Raycast, Alfred, Paste). Set `restore_clipboard = false` to keep the transcription in your clipboard instead.

## Troubleshooting

### "MySpeech is damaged and can't be opened"
This is macOS Gatekeeper blocking unsigned apps downloaded from the internet. Fix it by removing the quarantine attribute:
```bash
sudo xattr -cr /Applications/MySpeech.app
```
Alternatively, right-click the app and select "Open" to bypass Gatekeeper.

### Hotkey not working
- Grant **Accessibility** permission: System Settings > Privacy & Security > Accessibility > Add MySpeech.app
- Check logs: `tail -f ~/Library/Logs/MySpeech.log`

### No recording captured
- Grant **Microphone** permission in System Settings
- Check audio input device: `python -c "import sounddevice; print(sounddevice.query_devices())"`
- Adjust `min_level` in config if microphone is quiet

### Transcription shows wrong text
- Audio may be too short or quiet - Whisper can hallucinate on silence
- Speak clearly and close to microphone
- Check `min_duration` and `min_level` in config

### "MLX Audio Server not found" dialog
- Install mlx-audio server first (see [Requirements](#installing-mlx-audio-server))
- Ensure the server is running: `mlx_audio.server --port 8000`

### Server fails to start
- First run downloads the Whisper model (~1.5GB) - wait 2-3 minutes
- Check server logs: `tail -f ~/Library/Logs/MySpeech-server.log`
- Verify port 8000 is not in use: `lsof -i :8000`
- Start manually: `source ~/.mlx-audio-venv/bin/activate && mlx_audio.server --port 8000`

## License

MIT

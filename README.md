# MySpeech

A macOS speech-to-text app using [mlx-audio](https://github.com/Blaizzy/mlx-audio) on Apple Silicon. Hold a global hotkey to record, release to transcribe and auto-paste.

## Features

- **Hold to record** — Cmd+Ctrl+T to record, auto-transcribes and pastes on release
- **Auto-paste** — transcription is pasted directly into your active app
- **Clipboard restore** — original clipboard is restored after pasting; transcription stays in clipboard history
- **Language selection** — switch transcription language from the menu bar (or auto-detect)
- **Audio device selection** — pick any input device from the menu bar; auto-recovers if a device reconnects with a new index
- **Visual indicator** — yellow dot shows while recording, disappears immediately on release
- **Local processing** — Whisper via mlx-audio, no internet or cloud API required
- **Auto-start server** — launches mlx-audio automatically if it isn't running

## Requirements

- macOS 13+ on Apple Silicon (M1/M2/M3/M4)
- [mlx-audio](https://github.com/Blaizzy/mlx-audio) server running locally

### Installing the MLX Audio Server

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install mlx-audio
uv venv ~/.mlx-audio-venv --python 3.12
source ~/.mlx-audio-venv/bin/activate
uv pip install mlx-audio

# Start the server (first run downloads ~1.5 GB Whisper model)
mlx_audio.server --port 8000
```

> **Tip:** Keep the server running in a terminal tab, or add it to your shell startup.

## Installation

### Quick Install (Recommended)

```bash
curl -fsSL -H "Cache-Control: no-cache" https://raw.githubusercontent.com/antonpetrovmain/myspeech/main/install.sh | bash
```

To install to a custom directory (no admin password needed):

```bash
curl -fsSL -H "Cache-Control: no-cache" https://raw.githubusercontent.com/antonpetrovmain/myspeech/main/install.sh | bash -s -- --dir ~/tools
```

The script downloads the latest release, installs the app, and removes the Gatekeeper quarantine attribute automatically.

### Manual Install

1. Download `MySpeech-vX.X.X.zip` from the [latest release](https://github.com/antonpetrovmain/myspeech/releases)
2. Extract and install:
   ```bash
   unzip MySpeech-*.zip
   sudo mv MySpeech.app /Applications/
   sudo xattr -cr /Applications/MySpeech.app
   ```
3. Launch and grant permissions (see below)

### Development Setup

```bash
git clone https://github.com/antonpetrovmain/myspeech.git
cd myspeech
uv venv .venv
source .venv/bin/activate
uv pip install -e .
python main.py
```

## Permissions

Go to **System Settings > Privacy & Security** and enable:

1. **Accessibility** — required for hotkey capture and key suppression
2. **Microphone** — required for audio recording

Add `MySpeech.app` (or your terminal app if running from source) to both.

## Usage

| Action | Hotkey |
|---|---|
| Record & transcribe | Hold **Cmd+Ctrl+T**, release to stop |
| Open last recording | **Cmd+Ctrl+R** |
| Change language / device | Click the menu bar icon |
| View logs | Menu bar → Open Log File |

Logs are written to `~/Library/Logs/MySpeech.log`.

## Configuration

Settings live in `~/.config/myspeech/config.toml` (created on first run). Edit via **Menu Bar → Edit Settings...** or open the file directly.

```toml
[server]
url = "http://localhost:8000/v1"
model = "mlx-community/whisper-large-v3-turbo"
language = ""          # ISO 639-1 code (e.g. "en", "bg", "de"). Empty = auto-detect

[audio]
device = "default"     # "default" or a device index (e.g. 4)
gain = 1.0             # Boost quiet microphones (e.g. 2.0 = double volume)
save_recording = true  # Save last recording to recording_path (for debug/playback)
recording_path = "/tmp/myspeech_recording.wav"
min_duration = 0.5     # Reject recordings shorter than this (seconds)
min_level = 100        # Reject recordings below this average audio level

[hotkey]
modifiers = "cmd+ctrl" # Modifier keys: cmd, ctrl, alt, shift (joined by +)
record_key = "t"       # Hold this key (with modifiers) to record
open_recording_key = "r"
debounce_seconds = 0.5

[popup]
dot_size = 16
dot_color = "#ffcc00"
dot_alpha = 0.7

[clipboard]
paste_delay = 0.1      # Seconds to wait for target app to activate before pasting
restore_clipboard = true
restore_delay = 1.1    # Seconds before restoring clipboard (lets history apps capture transcription)
```

**`restore_clipboard`:** When enabled (default), your original clipboard is restored after pasting. The transcription remains in clipboard history (Raycast, Alfred, Paste, etc.). Set to `false` to keep the transcription in your clipboard.

## Building from Source

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
uv pip install pyinstaller

pyinstaller MySpeech.spec --clean
# Output: dist/MySpeech.app
```

## Troubleshooting

### "MySpeech is damaged and can't be opened"
Gatekeeper is blocking the unsigned app. Run:
```bash
sudo xattr -cr /Applications/MySpeech.app
```
Or right-click the app and choose **Open**.

### Hotkey not working
- Grant **Accessibility** permission (System Settings → Privacy & Security → Accessibility)
- Check logs: `tail -f ~/Library/Logs/MySpeech.log`

### No audio captured
- Grant **Microphone** permission in System Settings
- Check available devices: `python -c "import sounddevice; print(sounddevice.query_devices())"`
- If your mic is quiet, increase `gain` in config (e.g. `gain = 2.0`)
- Adjust `min_level` if recordings are being rejected

### Wrong transcription / hallucinations
- Whisper hallucinates on silence — speak clearly before releasing
- Increase `min_duration` or `min_level` to filter short/quiet recordings
- Set `language` explicitly instead of relying on auto-detect

### "MLX Audio Server not found"
- Install and start the mlx-audio server (see [Requirements](#installing-the-mlx-audio-server))
- Confirm it's running: `curl http://localhost:8000/v1/models`

### Server slow to start / first run
- The first run downloads the Whisper model (~1.5 GB) — wait a few minutes
- Check server logs: `tail -f ~/Library/Logs/MySpeech-server.log`
- Verify port 8000 is free: `lsof -i :8000`

## License

MIT

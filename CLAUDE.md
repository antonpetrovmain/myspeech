# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MySpeech is a macOS speech-to-text app using mlx-audio on Apple Silicon. Hold a global hotkey to record, release to transcribe and auto-paste.

## Commands

```bash
# Setup (using uv)
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# Run
python main.py

# Build app bundle
uv pip install pyinstaller
pyinstaller MySpeech.spec --clean
# Result: dist/MySpeech.app
```

## Architecture

**Entry point**: `main.py` → `myspeech/app.py:MySpeechApp`

**Components** (all in `myspeech/`):
- `app.py` - Main orchestrator, coordinates all components, handles hotkey callbacks
- `server.py` - Manages mlx-audio server lifecycle (auto-starts if needed)
- `hotkey.py` - Global hotkey detection using pynput with `darwin_intercept` for key suppression
- `recorder.py` - Audio capture via sounddevice with callback streaming, outputs WAV bytes
- `transcriber.py` - Sends audio to mlx-audio server using OpenAI-compatible API
- `clipboard.py` - Saves frontmost app, sets clipboard via pbcopy, pastes via AppleScript
- `popup.py` - Native macOS yellow dot indicator using AppKit
- `menubar.py` - Menu bar icon and status

**Configuration system**:
- `config.py` - Module-level constants loaded at import time, used throughout the app
- `myspeech/user_config.py` - Reads/writes user config file at `~/.config/myspeech/config.toml`
- Config values flow: `config.toml` → `user_config.get()` → `config.py` constants

**Threading model**:
- Main thread runs AppKit event loop (via PyObjCTools.AppHelper)
- All hotkey callbacks, recording, transcription, and clipboard operations run in daemon threads
- `Recorder` and `HotkeyListener` use locks for thread synchronization

## Key Implementation Details

- Hotkeys use virtual key codes (`key.vk`) not characters, making them keyboard-layout independent
- `_build_vk_to_char_map()` in `hotkey.py` uses Carbon's UCKeyTranslate to map VK codes to characters for the current keyboard layout
- `darwin_intercept` callback (using Quartz CGEvents) suppresses hotkey keys to prevent them leaking to other apps
- Without accessibility permissions, app starts without `darwin_intercept` to avoid system hang (hotkeys still work but leak to other apps)
- Audio recordings rejected if < 0.5 seconds or audio level < 100 (prevents silent recordings)
- On record start: saves frontmost app bundle ID. On stop: transcribes, sets clipboard, restores focus, pastes via Cmd+V

## Logs and Debug

- App log: `~/Library/Logs/MySpeech.log`
- Server log: `~/Library/Logs/MySpeech-server.log`
- Debug recording: Enable `save_recording = true` in config.toml, file saved to `/tmp/myspeech_recording.wav` (Cmd+Ctrl+R to open)

## Release Process

After a validated fix, run the full release pipeline:

1. Bump version in `myspeech/__init__.py`
2. Commit all changes
3. Push to remote
4. Build the app bundle: `pyinstaller MySpeech.spec --clean`
5. Zip: `cd dist && zip -r MySpeech-v<VERSION>.zip MySpeech.app`
6. Create GitHub release with tag and upload the zip: `gh release create v<VERSION> dist/MySpeech-v<VERSION>.zip --title "v<VERSION>" --notes "<changelog>"`

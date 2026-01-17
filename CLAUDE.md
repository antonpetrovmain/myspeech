# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MySpeech is a macOS speech-to-text app using mlx-audio on Apple Silicon. Hold a global hotkey to record, release to transcribe and auto-paste.

## Commands

```bash
# Setup
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .

# Run
python main.py
```

## Architecture

**Entry point**: `main.py` → `myspeech/app.py:MySpeechApp`

**Components** (all in `myspeech/`):
- `app.py` - Main orchestrator, coordinates all components, handles hotkey callbacks
- `server.py` - Manages mlx-audio server lifecycle (auto-starts if needed)
- `hotkey.py` - Global hotkey detection using pynput (uses virtual key codes for layout independence)
- `recorder.py` - Audio capture via sounddevice with callback streaming, outputs WAV bytes
- `transcriber.py` - Sends audio to mlx-audio server using OpenAI-compatible API
- `clipboard.py` - Saves frontmost app, sets clipboard via pbcopy, pastes via AppleScript
- `popup.py` - Tkinter "Recording..." indicator in top-right corner

**Threading model**:
- Main thread runs tkinter event loop
- All hotkey callbacks, recording, transcription, and clipboard operations run in daemon threads
- `Recorder` and `HotkeyListener` use locks for thread synchronization

**Configuration**: All settings in `config.py` (server URL, hotkey codes, audio settings, popup appearance)

## Key Implementation Details

- Hotkeys use virtual key codes (`key.vk`) not characters, making them keyboard-layout independent
- Audio recordings rejected if < 0.5 seconds or audio level < 100 (prevents silent recordings)
- On record start: saves frontmost app bundle ID. On stop: transcribes, sets clipboard, restores focus, pastes via Cmd+V
- Set `SAVE_RECORDING = True` in config to save recordings to `/tmp/myspeech_recording.wav` (use Cmd+Ctrl+R to open)

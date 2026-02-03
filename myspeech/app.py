import logging
import os
import subprocess
import sys
import signal
import threading
from pathlib import Path

import sounddevice as sd

import config

# Setup logging to file for packaged app
LOG_PATH = Path.home() / "Library/Logs/MySpeech.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

from myspeech.recorder import Recorder
from myspeech.transcriber import Transcriber
from myspeech.hotkey import HotkeyListener, check_accessibility_permissions, show_accessibility_dialog
from myspeech.popup import RecordingPopup
from myspeech.clipboard import ClipboardManager
from myspeech.server import ServerManager, get_system_memory, get_process_memory_mb, show_server_not_found_dialog
from myspeech.menubar import MenuBar, get_app_version


def show_no_audio_input_dialog():
    """Show a native macOS dialog when no audio input device is available."""
    try:
        from AppKit import NSAlert, NSAlertStyleWarning, NSApplication

        NSApplication.sharedApplication()

        alert = NSAlert.alloc().init()
        alert.setAlertStyle_(NSAlertStyleWarning)
        alert.setMessageText_("No Audio Input Device")
        alert.setInformativeText_(
            "MySpeech could not find a default audio input device.\n\n"
            "Please either:\n"
            "1. Set a default input device in System Settings → Sound → Input\n"
            "2. Or specify a device number in ~/.config/myspeech/config.toml:\n"
            "   [audio]\n"
            "   device = 2  # Replace with your device number\n\n"
            "Run 'python -c \"import sounddevice; print(sounddevice.query_devices())\"' "
            "to see available devices."
        )
        alert.addButtonWithTitle_("Open Sound Settings")
        alert.addButtonWithTitle_("Quit")

        response = alert.runModal()

        if response == 1000:
            subprocess.run(["open", "x-apple.systempreferences:com.apple.Sound-Settings.extension"], check=False)

    except Exception as e:
        log.warning(f"Could not show dialog: {e}")


class MySpeechApp:
    def __init__(self):
        self._server = ServerManager()
        self._recorder = Recorder()
        self._transcriber = Transcriber()
        self._popup = RecordingPopup()
        self._clipboard = ClipboardManager()
        self._menubar: MenuBar | None = None
        self._hotkey: HotkeyListener | None = None
        self._lock = threading.Lock()

    def _on_record_start(self):
        log.info("Hotkey pressed - starting recording")
        # Save frontmost app immediately (before any UI changes)
        threading.Thread(target=self._clipboard.save, daemon=True).start()

        # Start recording directly (we're already in a daemon thread)
        with self._lock:
            self._recorder.start()

        # Update menu bar to show recording status
        if self._menubar:
            self._menubar.set_recording(True)

        # Show popup (schedule on main thread for UI)
        self._popup.show()

    def _on_record_stop(self):
        # Stop recording directly (we're already in a daemon thread)
        with self._lock:
            audio_bytes = self._recorder.stop()

        # Update menu bar to show not recording
        if self._menubar:
            self._menubar.set_recording(False)

        if not audio_bytes:
            self._clipboard.restore()
            return

        # Transcribe in background to not block
        threading.Thread(
            target=self._process_transcription,
            args=(audio_bytes,),
            daemon=True,
        ).start()

    def _on_keys_released(self):
        """Called when all hotkey keys are released - safe to hide popup."""
        self._popup.hide()

    def _process_transcription(self, audio_bytes: bytes):
        log.info("Transcribing...")
        text = self._transcriber.transcribe(audio_bytes)

        if text:
            log.info(f"Result: {text}")
            self._clipboard.set_and_paste(text)
        else:
            log.warning("No transcription result.")
            self._clipboard.restore()

        # Show memory stats after transcription
        self._log_memory_stats()

    def _log_memory_stats(self):
        """Log current memory usage stats."""
        server_mb = self._server.get_memory_mb() or 0
        app_mb = get_process_memory_mb(os.getpid())
        mem = get_system_memory()
        if mem:
            total, used, _ = mem
            log.info(f"RAM: {used * 100 // total}% ({used:,} / {total:,} MB) | App: {app_mb} MB | MLX: {server_mb:,} MB")

    def _on_open_recording(self):
        try:
            subprocess.run(["open", config.RECORDING_PATH], check=False)
        except Exception:
            pass

    def run(self):
        log.info(f"MySpeech v{get_app_version()} starting...")

        # Ensure server is running
        if not self._server.start():
            log.error("Cannot start without mlx-audio server. Exiting.")
            show_server_not_found_dialog()
            os._exit(1)

        # Display server info
        log.info(f"Model: {config.WHISPER_MODEL}")
        self._log_memory_stats()

        log.info("MySpeech started. Cmd+Ctrl+T: record, Cmd+Ctrl+R: open recording")

        # Log audio input device
        if config.AUDIO_DEVICE is not None:
            device_info = sd.query_devices(config.AUDIO_DEVICE)
            log.info(f"Audio input: [{config.AUDIO_DEVICE}] {device_info['name']}")
        else:
            default_idx = sd.default.device[0]
            if default_idx < 0:
                log.error("No default audio input device found")
                show_no_audio_input_dialog()
                os._exit(1)
            device_info = sd.query_devices(default_idx)
            log.info(f"Audio input: Default ([{default_idx}] {device_info['name']})")

        # Pre-warm audio stream for instant recording start
        self._recorder.ensure_stream()

        # Setup native macOS app on main thread
        self._popup.setup()

        # Create menu bar (setup deferred to after event loop starts)
        self._menubar = MenuBar(self)

        def deferred_setup():
            self._menubar.setup(quit_callback=self._popup.stop)

            # Check accessibility permissions inside the event loop
            if not check_accessibility_permissions():
                log.warning("Accessibility permissions not granted")
                if not show_accessibility_dialog():
                    # User chose to open System Settings — quit cleanly
                    self._popup.stop()
                    return

            # Start hotkey listener in background thread
            self._hotkey = HotkeyListener(
                on_record_start=self._on_record_start,
                on_record_stop=self._on_record_stop,
                on_keys_released=self._on_keys_released,
                on_open_recording=self._on_open_recording,
            )
            self._hotkey.start()

        self._popup.schedule_delayed(100, deferred_setup)

        # Handle Ctrl+C
        def on_sigint(*args):
            self._popup.stop()

        signal.signal(signal.SIGINT, on_sigint)

        try:
            self._popup.run()
        finally:
            if self._hotkey:
                self._hotkey.stop()
            self._recorder._close_stream()
            self._server.stop()
            log.info("MySpeech stopped.")


def main():
    app = MySpeechApp()
    app.run()

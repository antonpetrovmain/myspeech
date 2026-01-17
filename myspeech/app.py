import subprocess
import threading
import signal
import sys

import sounddevice as sd

import config
from myspeech.recorder import Recorder
from myspeech.transcriber import Transcriber
from myspeech.hotkey import HotkeyListener
from myspeech.popup import RecordingPopup
from myspeech.clipboard import ClipboardManager
from myspeech.server import ServerManager


class MySpeechApp:
    def __init__(self):
        self._server = ServerManager()
        self._recorder = Recorder()
        self._transcriber = Transcriber()
        self._popup = RecordingPopup()
        self._clipboard = ClipboardManager()
        self._hotkey: HotkeyListener | None = None
        self._lock = threading.Lock()

    def _on_record_start(self):
        # Save frontmost app immediately (before any UI changes)
        threading.Thread(target=self._clipboard.save, daemon=True).start()

        def do_start():
            with self._lock:
                # Start recording immediately
                self._recorder.start()

            # Show popup after delay so user knows recording is active
            def show_popup():
                self._popup.show()

            self._popup.schedule_delayed(config.POPUP_DELAY_MS, show_popup)

        self._popup.schedule(do_start)

    def _on_record_stop(self):
        def do_stop():
            with self._lock:
                audio_bytes = self._recorder.stop()
                self._popup.hide()

                if not audio_bytes:
                    self._clipboard.restore()
                    return

                # Transcribe in background to not block
                threading.Thread(
                    target=self._process_transcription,
                    args=(audio_bytes,),
                    daemon=True,
                ).start()

        self._popup.schedule(do_stop)

    def _process_transcription(self, audio_bytes: bytes):
        text = self._transcriber.transcribe(audio_bytes)

        if text:
            self._clipboard.set_and_paste(text)
        else:
            self._clipboard.restore()

    def _on_open_recording(self):
        recording_path = "/tmp/myspeech_recording.wav"
        try:
            subprocess.run(["open", recording_path], check=False)
        except Exception:
            pass

    def run(self):
        # Ensure server is running
        if not self._server.start():
            print("Cannot start without mlx-omni-server. Exiting.")
            sys.exit(1)

        print("MySpeech started.")
        print("  Cmd+Ctrl+T: Hold to record, release to transcribe")
        print("  Cmd+Ctrl+R: Open last recording")
        print("  Ctrl+C: Quit")

        # Show available audio input devices
        print("\nAvailable input devices:")
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                default = " (DEFAULT)" if i == sd.default.device[0] else ""
                print(f"  [{i}] {d['name']}{default}")

        # Setup tkinter on main thread
        root = self._popup.setup()

        # Start hotkey listener in background thread
        self._hotkey = HotkeyListener(
            on_record_start=self._on_record_start,
            on_record_stop=self._on_record_stop,
            on_open_recording=self._on_open_recording,
        )
        self._hotkey.start()

        # Handle Ctrl+C
        def on_sigint(*args):
            self._popup.stop()

        signal.signal(signal.SIGINT, on_sigint)

        try:
            root.mainloop()
        finally:
            if self._hotkey:
                self._hotkey.stop()
            self._server.stop()
            print("\nMySpeech stopped.")


def main():
    app = MySpeechApp()
    app.run()

import subprocess
import time

import config


class ClipboardManager:
    def __init__(self):
        self._saved_app: str | None = None
        self._saved_clipboard_text: str | None = None

    def save(self):
        # Save the frontmost application's bundle identifier
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to get bundle identifier of first application process whose frontmost is true'],
                capture_output=True,
                text=True,
                timeout=2,
            )
            self._saved_app = result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            self._saved_app = None

        # Save current clipboard text if restore is enabled
        if config.RESTORE_CLIPBOARD:
            try:
                result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
                self._saved_clipboard_text = result.stdout if result.returncode == 0 else None
            except Exception:
                self._saved_clipboard_text = None

    def set_and_paste(self, text: str) -> bool:
        try:
            # Copy to clipboard using pbcopy
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
            )
            process.communicate(text.encode("utf-8"))

            # Restore focus to original app and paste
            if self._saved_app:
                # Activate the app using bundle identifier and paste
                script = f'''
                    tell application id "{self._saved_app}" to activate
                    delay {config.PASTE_DELAY}
                    tell application "System Events" to keystroke "v" using command down
                '''
                subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    timeout=3,
                )

            # Restore previous clipboard content after a delay
            # (allows clipboard history apps to capture the transcription)
            if config.RESTORE_CLIPBOARD and self._saved_clipboard_text is not None:
                try:
                    time.sleep(config.RESTORE_DELAY)
                    restore_process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                    restore_process.communicate(self._saved_clipboard_text.encode("utf-8"))
                except Exception:
                    pass
            self._saved_clipboard_text = None

            self._saved_app = None
            return process.returncode == 0
        except Exception:
            self._saved_app = None
            self._saved_clipboard_text = None
            return False

    def restore(self):
        # Just restore focus without pasting (used when no transcription)
        if self._saved_app:
            try:
                subprocess.run(
                    ["osascript", "-e", f'tell application id "{self._saved_app}" to activate'],
                    capture_output=True,
                    timeout=2,
                )
            except Exception:
                pass
        self._saved_app = None
        self._saved_clipboard_text = None

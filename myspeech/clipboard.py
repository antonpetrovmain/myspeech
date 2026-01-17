import subprocess

import config


class ClipboardManager:
    def __init__(self):
        self._saved_app: str | None = None

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

            return process.returncode == 0
        except Exception:
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

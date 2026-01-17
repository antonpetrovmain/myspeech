import threading
from typing import Callable
from pynput import keyboard

import config


class HotkeyListener:
    def __init__(
        self,
        on_record_start: Callable[[], None],
        on_record_stop: Callable[[], None],
    ):
        self._on_record_start = on_record_start
        self._on_record_stop = on_record_stop
        self._pressed_keys: set[str] = set()
        self._hotkey_active = False
        self._lock = threading.Lock()
        self._listener: keyboard.Listener | None = None

    def _normalize_key(self, key) -> str | None:
        try:
            if hasattr(key, "char") and key.char:
                char = key.char
                # Handle control characters (Ctrl+letter produces chr(1-26))
                if len(char) == 1 and ord(char) < 32:
                    # Convert control character back to letter (Ctrl+B = chr(2) -> 'b')
                    return chr(ord(char) + 96)
                return char.lower()
        except AttributeError:
            pass

        key_mapping = {
            keyboard.Key.cmd: "cmd",
            keyboard.Key.cmd_l: "cmd",
            keyboard.Key.cmd_r: "cmd",
            keyboard.Key.ctrl: "ctrl",
            keyboard.Key.ctrl_l: "ctrl",
            keyboard.Key.ctrl_r: "ctrl",
            keyboard.Key.alt: "alt",
            keyboard.Key.alt_l: "alt",
            keyboard.Key.alt_r: "alt",
            keyboard.Key.shift: "shift",
            keyboard.Key.shift_l: "shift",
            keyboard.Key.shift_r: "shift",
        }
        return key_mapping.get(key)

    def _check_hotkey(self) -> bool:
        required = config.HOTKEY_MODIFIERS | {config.HOTKEY_CHAR}
        return required <= self._pressed_keys

    def _on_press(self, key):
        normalized = self._normalize_key(key)
        if not normalized:
            return

        with self._lock:
            self._pressed_keys.add(normalized)

            if not self._hotkey_active and self._check_hotkey():
                self._hotkey_active = True
                threading.Thread(target=self._on_record_start, daemon=True).start()

    def _on_release(self, key):
        normalized = self._normalize_key(key)
        if not normalized:
            return

        with self._lock:
            self._pressed_keys.discard(normalized)

            if self._hotkey_active and not self._check_hotkey():
                self._hotkey_active = False
                threading.Thread(target=self._on_record_stop, daemon=True).start()

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

    def join(self):
        if self._listener:
            self._listener.join()

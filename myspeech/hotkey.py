import threading
import time
from typing import Callable

import Quartz
from pynput import keyboard

import config


class HotkeyListener:
    _MODIFIER_MAP = {
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

    def __init__(
        self,
        on_record_start: Callable[[], None],
        on_record_stop: Callable[[], None],
        on_keys_released: Callable[[], None] | None = None,
        on_open_recording: Callable[[], None] | None = None,
    ):
        self._on_record_start = on_record_start
        self._on_record_stop = on_record_stop
        self._on_keys_released = on_keys_released
        self._on_open_recording = on_open_recording
        self._pressed_modifiers: set[str] = set()
        self._pressed_key_codes: set[int] = set()
        self._hotkey_active = False
        self._waiting_for_release = False  # Track if we're waiting for all keys to be released
        self._last_record_end: float = 0
        self._lock = threading.Lock()
        self._listener: keyboard.Listener | None = None

    def _get_modifier(self, key) -> str | None:
        return self._MODIFIER_MAP.get(key)

    def _get_key_code(self, key) -> int | None:
        # Get the virtual key code (layout-independent)
        if hasattr(key, 'vk') and key.vk is not None:
            return key.vk
        return None

    def _check_modifiers(self) -> bool:
        return config.HOTKEY_MODIFIERS <= self._pressed_modifiers

    def _check_record_hotkey(self) -> bool:
        return self._check_modifiers() and config.HOTKEY_KEY_CODE in self._pressed_key_codes

    def _check_open_recording_hotkey(self) -> bool:
        return self._check_modifiers() and config.HOTKEY_OPEN_RECORDING_KEY_CODE in self._pressed_key_codes

    def _all_hotkey_keys_released(self) -> bool:
        """Check if all hotkey keys (modifiers + main key) are released."""
        # Check if main key is still pressed
        if config.HOTKEY_KEY_CODE in self._pressed_key_codes:
            return False
        # Check if any required modifier is still pressed
        for mod in config.HOTKEY_MODIFIERS:
            if mod in self._pressed_modifiers:
                return False
        return True

    def _on_press(self, key):
        modifier = self._get_modifier(key)
        key_code = self._get_key_code(key)

        with self._lock:
            if modifier:
                self._pressed_modifiers.add(modifier)
            if key_code is not None:
                self._pressed_key_codes.add(key_code)

            # Check open recording hotkey first (single press, not hold)
            if self._on_open_recording and self._check_open_recording_hotkey():
                threading.Thread(target=self._on_open_recording, daemon=True).start()
                return

            # Debounce: ignore if too soon after last recording
            if time.time() - self._last_record_end < config.HOTKEY_DEBOUNCE_SECONDS:
                return

            if not self._hotkey_active and self._check_record_hotkey():
                self._hotkey_active = True
                threading.Thread(target=self._on_record_start, daemon=True).start()

    def _on_release(self, key):
        modifier = self._get_modifier(key)
        key_code = self._get_key_code(key)

        with self._lock:
            if modifier:
                self._pressed_modifiers.discard(modifier)
            if key_code is not None:
                self._pressed_key_codes.discard(key_code)

            # Stop recording when hotkey is broken, but wait for all keys to be released
            if self._hotkey_active and not self._check_record_hotkey():
                self._hotkey_active = False
                self._waiting_for_release = True
                self._last_record_end = time.time()
                threading.Thread(target=self._on_record_stop, daemon=True).start()

            # Notify when all hotkey keys are released
            if self._waiting_for_release and self._all_hotkey_keys_released():
                self._waiting_for_release = False
                if self._on_keys_released:
                    threading.Thread(target=self._on_keys_released, daemon=True).start()

    def _create_darwin_intercept(self):
        """Create callback to suppress hotkey keys at system level."""
        def darwin_intercept(event_type, event):
            key_code = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventKeycode
            )

            # Suppress T and R keys while our hotkey is active or waiting for release
            with self._lock:
                if self._hotkey_active or self._waiting_for_release:
                    if key_code in (config.HOTKEY_KEY_CODE, config.HOTKEY_OPEN_RECORDING_KEY_CODE):
                        return None  # Suppress

            return event  # Pass through

        return darwin_intercept

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            darwin_intercept=self._create_darwin_intercept(),
        )
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

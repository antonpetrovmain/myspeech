import ctypes
import ctypes.util
import logging
import threading
import time
from typing import Callable

import Quartz
from pynput import keyboard

import config

log = logging.getLogger(__name__)


def _parse_modifiers(modifier_str: str) -> set[str]:
    """Parse modifier string like 'cmd+ctrl' into set {'cmd', 'ctrl'}."""
    return {m.strip().lower() for m in modifier_str.split('+')}


def _build_vk_to_char_map() -> dict[int, str]:
    """Build a mapping of VK codes to characters using the current keyboard layout."""
    vk_to_char = {}
    try:
        # Load Carbon framework for UCKeyTranslate
        carbon_path = ctypes.util.find_library('Carbon')
        if not carbon_path:
            return vk_to_char
        carbon = ctypes.CDLL(carbon_path)

        # Get current keyboard layout
        kTISPropertyUnicodeKeyLayoutData = ctypes.c_void_p.in_dll(
            carbon, 'kTISPropertyUnicodeKeyLayoutData'
        )
        TISCopyCurrentKeyboardInputSource = carbon.TISCopyCurrentKeyboardInputSource
        TISCopyCurrentKeyboardInputSource.restype = ctypes.c_void_p
        TISGetInputSourceProperty = carbon.TISGetInputSourceProperty
        TISGetInputSourceProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        TISGetInputSourceProperty.restype = ctypes.c_void_p

        source = TISCopyCurrentKeyboardInputSource()
        if not source:
            return vk_to_char

        layout_data = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData)
        if not layout_data:
            return vk_to_char

        # Get the actual data pointer from CFData
        CFDataGetBytePtr = carbon.CFDataGetBytePtr
        CFDataGetBytePtr.argtypes = [ctypes.c_void_p]
        CFDataGetBytePtr.restype = ctypes.c_void_p
        layout_ptr = CFDataGetBytePtr(layout_data)
        if not layout_ptr:
            return vk_to_char

        # UCKeyTranslate function
        UCKeyTranslate = carbon.UCKeyTranslate
        UCKeyTranslate.argtypes = [
            ctypes.c_void_p,  # keyLayoutPtr
            ctypes.c_uint16,  # virtualKeyCode
            ctypes.c_uint16,  # keyAction
            ctypes.c_uint32,  # modifierKeyState
            ctypes.c_uint32,  # keyboardType
            ctypes.c_uint32,  # keyTranslateOptions
            ctypes.POINTER(ctypes.c_uint32),  # deadKeyState
            ctypes.c_uint8,   # maxStringLength
            ctypes.POINTER(ctypes.c_uint8),   # actualStringLength
            ctypes.c_void_p,  # unicodeString
        ]
        UCKeyTranslate.restype = ctypes.c_int32

        kUCKeyActionDown = 0
        kUCKeyTranslateNoDeadKeysBit = 0

        # Try all VK codes 0-50 (covers most letter keys)
        for vk in range(51):
            dead_key_state = ctypes.c_uint32(0)
            actual_length = ctypes.c_uint8(0)
            unicode_string = (ctypes.c_uint16 * 4)()

            result = UCKeyTranslate(
                layout_ptr,
                ctypes.c_uint16(vk),
                ctypes.c_uint16(kUCKeyActionDown),
                ctypes.c_uint32(0),  # No modifiers
                ctypes.c_uint32(0),  # LMGetKbdType() - 0 works for current
                ctypes.c_uint32(kUCKeyTranslateNoDeadKeysBit),
                ctypes.byref(dead_key_state),
                ctypes.c_uint8(4),
                ctypes.byref(actual_length),
                unicode_string,
            )

            if result == 0 and actual_length.value == 1:
                char = chr(unicode_string[0]).lower()
                if char.isalpha():
                    vk_to_char[vk] = char

        log.debug(f"Built VK->char map with {len(vk_to_char)} entries")
    except Exception as e:
        log.warning(f"Failed to build VK->char map: {e}")

    return vk_to_char


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

        # Parse modifiers from config string
        self._required_modifiers = _parse_modifiers(config.HOTKEY_MODIFIERS)

        # Build VK -> char mapping at startup using keyboard layout
        self._vk_to_char = _build_vk_to_char_map()

        # Build reverse mapping (char -> VK) for configured hotkeys
        char_to_vk = {v: k for k, v in self._vk_to_char.items()}
        self._record_key_vk = char_to_vk.get(config.HOTKEY_KEY.lower())
        self._open_key_vk = char_to_vk.get(config.HOTKEY_OPEN_RECORDING_KEY.lower())

        if self._record_key_vk is not None:
            log.info(f"Record hotkey: VK {self._record_key_vk} for '{config.HOTKEY_KEY}'")
        else:
            log.warning(f"Could not find VK code for record key '{config.HOTKEY_KEY}'")

        if self._open_key_vk is not None:
            log.info(f"Open recording hotkey: VK {self._open_key_vk} for '{config.HOTKEY_OPEN_RECORDING_KEY}'")
        else:
            log.warning(f"Could not find VK code for open recording key '{config.HOTKEY_OPEN_RECORDING_KEY}'")

    def _get_modifier(self, key) -> str | None:
        return self._MODIFIER_MAP.get(key)

    def _get_key_code(self, key) -> int | None:
        # Get the virtual key code (layout-independent)
        if hasattr(key, 'vk') and key.vk is not None:
            return key.vk
        return None

    def _check_modifiers(self) -> bool:
        return self._required_modifiers <= self._pressed_modifiers

    def _check_record_hotkey(self) -> bool:
        if self._record_key_vk is None:
            return False
        return self._check_modifiers() and self._record_key_vk in self._pressed_key_codes

    def _check_open_recording_hotkey(self) -> bool:
        if self._open_key_vk is None:
            return False
        return self._check_modifiers() and self._open_key_vk in self._pressed_key_codes

    def _all_hotkey_keys_released(self) -> bool:
        """Check if all hotkey keys (modifiers + main key) are released."""
        # Check if main key is still pressed
        if self._record_key_vk is not None and self._record_key_vk in self._pressed_key_codes:
            return False
        # Check if any required modifier is still pressed
        for mod in self._required_modifiers:
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
                log.info("Record hotkey detected")
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

            # Suppress hotkey keys while our hotkey is active or waiting for release
            with self._lock:
                if self._hotkey_active or self._waiting_for_release:
                    suppress_keys = set()
                    if self._record_key_vk is not None:
                        suppress_keys.add(self._record_key_vk)
                    if self._open_key_vk is not None:
                        suppress_keys.add(self._open_key_vk)
                    if key_code in suppress_keys:
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

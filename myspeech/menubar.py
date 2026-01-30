import logging
import subprocess
from pathlib import Path

import config
from myspeech.recorder import get_input_devices, get_default_input_device

log = logging.getLogger(__name__)

LANGUAGES = [
    ("", "Auto-detect"),
    ("en", "English"),
    ("bg", "Bulgarian"),
]


def get_app_version() -> str:
    """Get the app version from Info.plist (bundled app) or return default."""
    try:
        # Try to read from app bundle's Info.plist
        import sys
        if getattr(sys, 'frozen', False):
            # Running as bundled app
            app_path = Path(sys.executable).parent.parent
            plist_path = app_path / "Info.plist"
            if plist_path.exists():
                result = subprocess.run(
                    ["defaults", "read", str(plist_path), "CFBundleShortVersionString"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
    except Exception:
        pass
    return "dev"

# Global to hold reference to delegate (prevent garbage collection)
_delegate = None
_status_item = None
_audio_menu_items = []
_language_menu_items = []


def _build_submenu(title, choices, action, delegate, current_value, NSMenu, NSMenuItem, NSOnState, NSOffState):
    """Build an NSMenu submenu with radio-style checkmarks.

    Args:
        title: Menu title.
        choices: List of (tag, value, label) tuples.
        action: ObjC selector string (e.g. "selectLanguage:").
        delegate: Menu delegate target.
        current_value: Currently selected value to checkmark.

    Returns:
        (parent_item, menu_items) where menu_items is [(tag, value, NSMenuItem), ...].
    """
    parent = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, "")
    menu = NSMenu.alloc().initWithTitle_(title)
    items = []

    for tag, value, label in choices:
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(label, action, "")
        item.setTarget_(delegate)
        item.setTag_(tag)
        item.setState_(NSOnState if value == current_value else NSOffState)
        menu.addItem_(item)
        items.append((tag, value, item))

    parent.setSubmenu_(menu)
    return parent, items


def _update_submenu_checkmarks(menu_items, selected_value, NSOnState, NSOffState):
    """Update checkmarks in a submenu, checking the item matching selected_value."""
    for _tag, value, item in menu_items:
        item.setState_(NSOnState if value == selected_value else NSOffState)


class MenuBar:
    """macOS menu bar integration using NSStatusBar."""

    def __init__(self, app_instance):
        self._app = app_instance
        self._recording = False
        self._quit_callback = None
        self._is_setup = False
        self._current_device = None  # None = default

    def setup(self, quit_callback=None):
        """Set up the menu bar."""
        global _delegate, _status_item, _audio_menu_items, _language_menu_items

        self._quit_callback = quit_callback
        menu_bar_instance = self

        try:
            from AppKit import NSStatusBar, NSMenu, NSMenuItem, NSImage, NSObject, NSOnState, NSOffState
            import objc

            class MenuBarDelegate(NSObject):
                """Delegate to handle menu actions."""

                quit_callback = None
                menubar = None

                def openLog_(self, sender):
                    log_path = Path.home() / "Library/Logs/MySpeech.log"
                    if log_path.exists():
                        subprocess.run(["open", str(log_path)], check=False)

                def openRecording_(self, sender):
                    recording_path = Path(config.RECORDING_PATH)
                    if recording_path.exists():
                        subprocess.run(["open", str(recording_path)], check=False)

                def openSettings_(self, sender):
                    from myspeech.user_config import CONFIG_FILE
                    subprocess.run(["open", str(CONFIG_FILE)], check=False)

                def selectLanguage_(self, sender):
                    tag = sender.tag()
                    if self.menubar:
                        self.menubar._select_language(tag)

                def selectAudioDevice_(self, sender):
                    device_idx = sender.tag()
                    device = None if device_idx == -1 else device_idx
                    if self.menubar:
                        self.menubar._select_device(device)

                def quitApp_(self, sender):
                    import os
                    os._exit(0)

            MenuBarDelegate.quit_callback = quit_callback
            MenuBarDelegate.menubar = menu_bar_instance

            status_bar = NSStatusBar.systemStatusBar()
            _status_item = status_bar.statusItemWithLength_(-1)

            icon_path = Path(__file__).parent.parent / "resources" / "menubar_icon.png"
            if icon_path.exists():
                image = NSImage.alloc().initByReferencingFile_(str(icon_path))
                image.setSize_((16, 16))
                _status_item.setImage_(image)

            _delegate = MenuBarDelegate.alloc().init()

            menu = NSMenu.alloc().initWithTitle_("MySpeech")

            # Version
            version_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"MySpeech v{get_app_version()}", None, ""
            )
            version_item.setEnabled_(False)
            menu.addItem_(version_item)

            # Server status
            server_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Server: Running", None, ""
            )
            server_item.setEnabled_(False)
            menu.addItem_(server_item)

            menu.addItem_(NSMenuItem.separatorItem())

            # Action items
            for title, action in [("Open Log File", "openLog:"),
                                  ("Open Last Recording", "openRecording:"),
                                  ("Edit Settings...", "openSettings:")]:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, "")
                item.setTarget_(_delegate)
                menu.addItem_(item)

            menu.addItem_(NSMenuItem.separatorItem())

            # Language submenu
            lang_choices = [(i, code, label) for i, (code, label) in enumerate(LANGUAGES)]
            lang_parent, _language_menu_items = _build_submenu(
                "Language", lang_choices, "selectLanguage:", _delegate,
                config.LANGUAGE, NSMenu, NSMenuItem, NSOnState, NSOffState,
            )
            menu.addItem_(lang_parent)

            menu.addItem_(NSMenuItem.separatorItem())

            # Audio input submenu
            default_idx = get_default_input_device()
            devices = get_input_devices()
            default_name = next((name for idx, name in devices if idx == default_idx), "System Default")
            configured_device = config.AUDIO_DEVICE
            self._current_device = configured_device

            # Build choices: default (-1, None) + all devices
            audio_choices = [(-1, None, f"Default ({default_name})")]
            audio_choices += [(idx, idx, f"[{idx}] {name}") for idx, name in devices]

            audio_parent, _audio_menu_items = _build_submenu(
                "Audio Input", audio_choices, "selectAudioDevice:", _delegate,
                configured_device, NSMenu, NSMenuItem, NSOnState, NSOffState,
            )
            menu.addItem_(audio_parent)

            menu.addItem_(NSMenuItem.separatorItem())

            # Quit
            quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Quit MySpeech", "quitApp:", ""
            )
            quit_item.setTarget_(_delegate)
            menu.addItem_(quit_item)

            _status_item.setMenu_(menu)
            self._is_setup = True
            log.info("Menu bar initialized")

        except Exception as e:
            log.warning(f"Could not setup menu bar: {e}")

    def set_recording(self, is_recording: bool):
        """Update menu bar to show recording status."""
        self._recording = is_recording

    def update_server_status(self, status: str):
        """Update server status in menu."""
        pass

    def _select_language(self, tag: int):
        """Select a transcription language."""
        try:
            from AppKit import NSOnState, NSOffState
        except ImportError:
            return

        code = LANGUAGES[tag][0]
        _update_submenu_checkmarks(_language_menu_items, code, NSOnState, NSOffState)

        config.LANGUAGE = code

        from myspeech import user_config
        user_config.set("server", "language", code)
        log.info(f"Language changed to: {code or 'auto-detect'}")

    def _select_device(self, device_index: int | None):
        """Select an audio input device."""
        try:
            from AppKit import NSOnState, NSOffState
        except ImportError:
            return

        self._current_device = device_index
        _update_submenu_checkmarks(_audio_menu_items, device_index, NSOnState, NSOffState)

        config.AUDIO_DEVICE = device_index
        if self._app and hasattr(self._app, '_recorder'):
            self._app._recorder.set_device(device_index)
            device_name = "Default" if device_index is None else f"[{device_index}]"
            log.info(f"Audio input changed to: {device_name}")

        from myspeech import user_config
        config_value = "default" if device_index is None else device_index
        user_config.set("audio", "device", config_value)

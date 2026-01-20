import logging
import subprocess
from pathlib import Path

import config
from myspeech.recorder import get_input_devices, get_default_input_device

log = logging.getLogger(__name__)


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
_audio_menu = None
_audio_menu_items = []


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
        global _delegate, _status_item, _audio_menu, _audio_menu_items

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

                def selectAudioDevice_(self, sender):
                    # Get device index from tag (-1 means default)
                    device_idx = sender.tag()
                    device = None if device_idx == -1 else device_idx
                    if self.menubar:
                        self.menubar._select_device(device)

                def quitApp_(self, sender):
                    # Use os._exit to avoid tkinter thread issues
                    import os
                    os._exit(0)

            MenuBarDelegate.quit_callback = quit_callback
            MenuBarDelegate.menubar = menu_bar_instance

            # Get the system status bar
            status_bar = NSStatusBar.systemStatusBar()

            # Create status item
            _status_item = status_bar.statusItemWithLength_(-1)

            # Get icon and set it
            icon_path = Path(__file__).parent.parent / "resources" / "menubar_icon.png"
            if icon_path.exists():
                image = NSImage.alloc().initByReferencingFile_(str(icon_path))
                image.setSize_((16, 16))
                _status_item.setImage_(image)

            # Create delegate for menu actions
            _delegate = MenuBarDelegate.alloc().init()

            # Create menu
            menu = NSMenu.alloc().initWithTitle_("MySpeech")

            # Version item
            version = get_app_version()
            version_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"MySpeech v{version}", None, ""
            )
            version_item.setEnabled_(False)
            menu.addItem_(version_item)

            # Server status item
            server_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Server: Running", None, ""
            )
            server_item.setEnabled_(False)
            menu.addItem_(server_item)

            # Separator
            menu.addItem_(NSMenuItem.separatorItem())

            # Open log file
            open_log_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Open Log File", "openLog:", ""
            )
            open_log_item.setTarget_(_delegate)
            menu.addItem_(open_log_item)

            # Open last recording
            open_rec_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Open Last Recording", "openRecording:", ""
            )
            open_rec_item.setTarget_(_delegate)
            menu.addItem_(open_rec_item)

            # Separator
            menu.addItem_(NSMenuItem.separatorItem())

            # Audio input device submenu
            audio_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Audio Input", None, ""
            )
            _audio_menu = NSMenu.alloc().initWithTitle_("Audio Input")
            _audio_menu_items = []

            # Add "Default" option
            default_idx = get_default_input_device()
            devices = get_input_devices()
            default_name = next((name for idx, name in devices if idx == default_idx), "System Default")

            # Get configured device from config
            configured_device = config.AUDIO_DEVICE  # None means default
            self._current_device = configured_device

            default_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"Default ({default_name})", "selectAudioDevice:", ""
            )
            default_item.setTarget_(_delegate)
            default_item.setTag_(-1)  # -1 means default
            default_item.setState_(NSOnState if configured_device is None else NSOffState)
            _audio_menu.addItem_(default_item)
            _audio_menu_items.append((-1, default_item))

            _audio_menu.addItem_(NSMenuItem.separatorItem())

            # Add all input devices
            for idx, name in devices:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    f"[{idx}] {name}", "selectAudioDevice:", ""
                )
                item.setTarget_(_delegate)
                item.setTag_(idx)
                item.setState_(NSOnState if configured_device == idx else NSOffState)
                _audio_menu.addItem_(item)
                _audio_menu_items.append((idx, item))

            audio_item.setSubmenu_(_audio_menu)
            menu.addItem_(audio_item)

            # Separator
            menu.addItem_(NSMenuItem.separatorItem())

            # Quit
            quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Quit MySpeech", "quitApp:", ""
            )
            quit_item.setTarget_(_delegate)
            menu.addItem_(quit_item)

            # Set menu
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

    def _select_device(self, device_index: int | None):
        """Select an audio input device."""
        global _audio_menu_items

        try:
            from AppKit import NSOnState, NSOffState
        except ImportError:
            return

        self._current_device = device_index

        # Update checkmarks
        tag_to_find = -1 if device_index is None else device_index
        for tag, item in _audio_menu_items:
            if tag == tag_to_find:
                item.setState_(NSOnState)
            else:
                item.setState_(NSOffState)

        # Update the recorder
        if self._app and hasattr(self._app, '_recorder'):
            self._app._recorder.set_device(device_index)
            device_name = "Default" if device_index is None else f"[{device_index}]"
            log.info(f"Audio input changed to: {device_name}")

        # Persist to config file
        from myspeech import user_config
        config_value = "default" if device_index is None else device_index
        user_config.set("audio", "device", config_value)

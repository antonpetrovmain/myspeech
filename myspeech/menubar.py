import logging
import subprocess
from pathlib import Path

import config

log = logging.getLogger(__name__)

# Global to hold reference to delegate (prevent garbage collection)
_delegate = None
_status_item = None


class MenuBar:
    """macOS menu bar integration using NSStatusBar."""

    def __init__(self, app_instance):
        self._app = app_instance
        self._recording = False
        self._quit_callback = None
        self._is_setup = False

    def setup(self, quit_callback=None):
        """Set up the menu bar."""
        global _delegate, _status_item

        self._quit_callback = quit_callback

        try:
            from AppKit import NSStatusBar, NSMenu, NSMenuItem, NSImage, NSObject
            import objc

            class MenuBarDelegate(NSObject):
                """Delegate to handle menu actions."""

                quit_callback = None

                def openLog_(self, sender):
                    log_path = Path.home() / "Library/Logs/MySpeech.log"
                    if log_path.exists():
                        subprocess.run(["open", str(log_path)], check=False)

                def openRecording_(self, sender):
                    recording_path = Path(config.RECORDING_PATH)
                    if recording_path.exists():
                        subprocess.run(["open", str(recording_path)], check=False)

                def quitApp_(self, sender):
                    # Use os._exit to avoid tkinter thread issues
                    import os
                    os._exit(0)

            MenuBarDelegate.quit_callback = quit_callback

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

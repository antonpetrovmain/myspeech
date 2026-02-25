from typing import Callable
import logging
import threading

log = logging.getLogger(__name__)


class AppKitRunner:
    """Manages the native macOS AppKit event loop."""

    def __init__(self):
        self._app = None

    def setup(self):
        """Initialize the shared NSApplication."""
        from AppKit import NSApplication
        self._app = NSApplication.sharedApplication()
        return self

    def schedule(self, callback: Callable[[], None]):
        """Schedule a callback on the main thread."""
        from PyObjCTools import AppHelper
        AppHelper.callAfter(callback)

    def schedule_delayed(self, delay_ms: int, callback: Callable[[], None]):
        """Schedule a delayed callback."""
        from PyObjCTools import AppHelper
        AppHelper.callLater(delay_ms / 1000.0, callback)

    def run(self):
        """Run the main event loop."""
        from PyObjCTools import AppHelper
        AppHelper.runEventLoop()

    def stop(self):
        """Stop the main event loop."""
        from PyObjCTools import AppHelper
        AppHelper.stopEventLoop()

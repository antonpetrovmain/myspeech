import tkinter as tk
from typing import Callable
import logging

import config

log = logging.getLogger(__name__)

# Global references to prevent garbage collection
_dot_window = None
_dot_view = None


class RecordingPopup:
    """Recording indicator using native macOS NSWindow for true transparency."""

    def __init__(self):
        self._root: tk.Tk | None = None
        self._visible = False
        self._ns_window = None

    def setup(self) -> tk.Tk:
        # Create a hidden tkinter root for the event loop
        self._root = tk.Tk()
        self._root.withdraw()  # Hide the tkinter window completely

        # Create native macOS window for the dot
        self._setup_native_dot()

        return self._root

    def _setup_native_dot(self):
        """Create a native macOS window with true transparency."""
        global _dot_window, _dot_view

        try:
            from AppKit import (
                NSWindow, NSView, NSColor, NSBezierPath,
                NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
                NSFloatingWindowLevel, NSScreen
            )
            from Foundation import NSRect, NSPoint, NSSize

            size = config.POPUP_DOT_SIZE

            # Get screen dimensions
            screen = NSScreen.mainScreen()
            screen_frame = screen.frame()
            screen_width = screen_frame.size.width

            # Position in top-right corner (8px from edges)
            x = screen_width - size - 8
            y = screen_frame.size.height - size - 8 - 25  # Account for menu bar (~25px)

            # Create the window
            frame = NSRect(NSPoint(x, y), NSSize(size, size))
            _dot_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                frame,
                NSWindowStyleMaskBorderless,
                NSBackingStoreBuffered,
                False
            )

            # Make window transparent
            _dot_window.setOpaque_(False)
            _dot_window.setBackgroundColor_(NSColor.clearColor())
            _dot_window.setLevel_(NSFloatingWindowLevel)  # Always on top
            _dot_window.setIgnoresMouseEvents_(True)  # Click-through
            _dot_window.setAlphaValue_(config.POPUP_DOT_ALPHA)

            # Create custom view that draws the dot
            class DotView(NSView):
                def drawRect_(self, rect):
                    # Parse hex color
                    color_hex = config.POPUP_DOT_COLOR.lstrip('#')
                    r = int(color_hex[0:2], 16) / 255.0
                    g = int(color_hex[2:4], 16) / 255.0
                    b = int(color_hex[4:6], 16) / 255.0

                    color = NSColor.colorWithRed_green_blue_alpha_(r, g, b, 1.0)
                    color.setFill()

                    # Draw circle
                    bounds = self.bounds()
                    path = NSBezierPath.bezierPathWithOvalInRect_(bounds)
                    path.fill()

            _dot_view = DotView.alloc().initWithFrame_(NSRect(NSPoint(0, 0), NSSize(size, size)))
            _dot_window.setContentView_(_dot_view)

            self._ns_window = _dot_window
            log.info("Native dot indicator initialized")

        except Exception as e:
            log.warning(f"Could not create native dot window: {e}")
            self._ns_window = None

    def show(self):
        if not self._visible:
            self._visible = True
            if self._ns_window:
                # Dispatch to main thread for thread safety
                self._ns_window.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "orderFront:", None, False
                )

    def hide(self):
        if self._visible:
            self._visible = False
            if self._ns_window:
                # Dispatch to main thread for thread safety
                self._ns_window.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "orderOut:", None, False
                )

    def schedule(self, callback: Callable[[], None]):
        """Schedule a callback on the tkinter main thread."""
        if self._root:
            self._root.after(0, callback)

    def schedule_delayed(self, delay_ms: int, callback: Callable[[], None]):
        if self._root:
            self._root.after(delay_ms, callback)

    def stop(self):
        if self._root:
            self._root.after(0, self._root.quit)

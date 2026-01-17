import tkinter as tk
from typing import Callable

import config


class RecordingPopup:
    def __init__(self):
        self._root: tk.Tk | None = None
        self._visible = False

    def setup(self) -> tk.Tk:
        self._root = tk.Tk()
        self._root.overrideredirect(True)  # Borderless
        self._root.attributes("-topmost", True)  # Always on top
        self._root.attributes("-alpha", 0.9)  # Slight transparency

        # Position in top-right corner
        screen_width = self._root.winfo_screenwidth()
        x = screen_width - config.POPUP_WIDTH - 20
        y = 40

        self._root.geometry(f"{config.POPUP_WIDTH}x{config.POPUP_HEIGHT}+{x}+{y}")
        self._root.configure(bg=config.POPUP_BG_COLOR)

        label = tk.Label(
            self._root,
            text=config.POPUP_TEXT,
            bg=config.POPUP_BG_COLOR,
            fg=config.POPUP_TEXT_COLOR,
            font=("Helvetica", 14, "bold"),
        )
        label.pack(expand=True)

        # Start hidden
        self._root.withdraw()

        return self._root

    def show(self):
        if self._root and not self._visible:
            self._visible = True
            self._root.after(0, self._do_show)

    def _do_show(self):
        if self._root:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()  # Take focus to capture key events

    def hide(self):
        if self._root and self._visible:
            self._visible = False
            self._root.after(0, self._root.withdraw)

    def schedule(self, callback: Callable[[], None]):
        if self._root:
            self._root.after(0, callback)

    def schedule_delayed(self, delay_ms: int, callback: Callable[[], None]):
        if self._root:
            self._root.after(delay_ms, callback)

    def stop(self):
        if self._root:
            self._root.after(0, self._root.quit)

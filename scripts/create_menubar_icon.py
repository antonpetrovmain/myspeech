#!/usr/bin/env python
"""Generate a menu bar icon for MySpeech."""

from PIL import Image, ImageDraw
from pathlib import Path

# Icon size for menu bar (22x22 is standard for macOS)
SIZE = 22
ICON_PATH = Path(__file__).parent.parent / "resources" / "menubar_icon.png"

# Create a new image with transparent background
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a simple waveform icon
# Use black color (will be templated by macOS for menu bar appearance)
# Draw a microphone-like waveform
line_width = 2
margin = 3

# Draw 3 vertical lines representing a waveform/microphone
positions = [
    (5, 8, 5, 14),      # Left line (shorter)
    (11, 5, 11, 17),    # Middle line (taller)
    (17, 8, 17, 14),    # Right line (shorter)
]

for x1, y1, x2, y2 in positions:
    draw.line((x1, y1, x2, y2), fill=(255, 0, 0, 255), width=line_width)

# Ensure the icon directory exists
ICON_PATH.parent.mkdir(parents=True, exist_ok=True)

# Save the icon
img.save(ICON_PATH)
print(f"Created menu bar icon: {ICON_PATH}")

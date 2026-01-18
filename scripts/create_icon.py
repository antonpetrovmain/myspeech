#!/usr/bin/env python3
"""Generate a waveform icon for MySpeech app."""

import math
from pathlib import Path

# Try PIL first, fall back to manual PNG creation
try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def create_waveform_icon_pil(size: int = 1024) -> Image.Image:
    """Create a waveform icon using PIL."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle with gradient-like effect (red theme to match popup)
    padding = size // 16
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill='#CC0000'
    )

    # Draw waveform bars
    num_bars = 7
    bar_width = size // 16
    gap = size // 24
    total_width = num_bars * bar_width + (num_bars - 1) * gap
    start_x = (size - total_width) // 2
    center_y = size // 2

    # Heights for waveform pattern (symmetric, taller in middle)
    heights = [0.25, 0.45, 0.7, 0.9, 0.7, 0.45, 0.25]
    max_height = size // 3

    for i, h in enumerate(heights):
        bar_height = int(max_height * h)
        x = start_x + i * (bar_width + gap)
        y1 = center_y - bar_height // 2
        y2 = center_y + bar_height // 2

        # Rounded rectangle for each bar
        draw.rounded_rectangle(
            [x, y1, x + bar_width, y2],
            radius=bar_width // 2,
            fill='white'
        )

    return img


def create_iconset(icon_path: Path, output_dir: Path):
    """Create .iconset folder with all required sizes."""
    if not HAS_PIL:
        raise RuntimeError("PIL/Pillow required: pip install Pillow")

    iconset_dir = output_dir / "MySpeech.iconset"
    iconset_dir.mkdir(parents=True, exist_ok=True)

    # Required sizes for macOS iconset
    sizes = [16, 32, 64, 128, 256, 512, 1024]

    # Create base icon at highest resolution
    base_icon = create_waveform_icon_pil(1024)

    for size in sizes:
        # Standard resolution
        resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(iconset_dir / f"icon_{size}x{size}.png")

        # @2x resolution (Retina)
        if size <= 512:
            resized_2x = base_icon.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
            resized_2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")

    print(f"Created iconset at {iconset_dir}")
    return iconset_dir


def main():
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    resources_dir = project_dir / "resources"
    resources_dir.mkdir(exist_ok=True)

    # Create iconset
    iconset_dir = create_iconset(None, resources_dir)

    # Convert to .icns using iconutil
    import subprocess
    icns_path = resources_dir / "MySpeech.icns"
    result = subprocess.run(
        ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"Created {icns_path}")
        # Clean up iconset folder
        import shutil
        shutil.rmtree(iconset_dir)
    else:
        print(f"Error creating icns: {result.stderr}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

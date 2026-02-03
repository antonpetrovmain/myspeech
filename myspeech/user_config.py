"""User configuration file management.

Creates and loads user configuration from ~/.config/myspeech/config.toml
"""

import logging
import tomllib
from pathlib import Path

log = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".config" / "myspeech"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = """\
# MySpeech Configuration
# Edit this file to customize settings. Delete to reset to defaults.

[server]
url = "http://localhost:8000/v1"
model = "mlx-community/whisper-large-v3-turbo"
language = ""  # ISO 639-1 code (e.g., "en", "bg", "de"). Empty = auto-detect

[audio]
sample_rate = 16000
channels = 1
device = "default"  # "default" or device index (e.g., 4)
gain = 1.0  # Audio gain multiplier (1.0 = no change, 2.0 = double volume)
save_recording = true
recording_path = "/tmp/myspeech_recording.wav"
min_duration = 0.5  # Minimum seconds to accept recording
min_level = 100  # Minimum audio level (prevents silent recordings)

[hotkey]
# Modifiers: cmd, ctrl, alt, shift (separated by +)
modifiers = "cmd+ctrl"
record_key = "t"  # Hold to record (Cmd+Ctrl+T)
open_recording_key = "r"  # Open last recording (Cmd+Ctrl+R)
debounce_seconds = 0.5

[popup]
dot_size = 16
dot_color = "#ffcc00"
dot_alpha = 0.7

[clipboard]
# paste_delay: Seconds to wait for target app to activate before pasting
paste_delay = 0.1
# restore_clipboard: If true, restores your original clipboard after pasting transcription.
# The transcription remains in clipboard history (accessible via Raycast, Alfred, Paste, etc.)
restore_clipboard = true
# restore_delay: Seconds to wait before restoring clipboard. Allows clipboard history apps
# to capture the transcription. Increase if your clipboard manager isn't capturing it.
restore_delay = 1.1
"""


def ensure_config_exists() -> None:
    """Create default config file if it doesn't exist."""
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(DEFAULT_CONFIG)
        log.info(f"Created default config at {CONFIG_FILE}")


def load_config() -> dict:
    """Load configuration from user config file."""
    ensure_config_exists()
    try:
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        log.warning(f"Failed to load config from {CONFIG_FILE}: {e}")
        return {}


def get(section: str, key: str, default):
    """Get a config value with fallback to default."""
    config = load_config()
    return config.get(section, {}).get(key, default)


def set(section: str, key: str, value) -> bool:
    """Update a config value in the config file.

    Uses line-by-line approach to preserve comments and formatting.
    Returns True if successful.
    """
    ensure_config_exists()
    try:
        content = CONFIG_FILE.read_text()
        lines = content.split('\n')

        # Format the value for TOML
        if isinstance(value, bool):
            toml_value = "true" if value else "false"
        elif isinstance(value, str):
            toml_value = f'"{value}"'
        elif isinstance(value, (int, float)):
            toml_value = str(value)
        else:
            toml_value = f'"{value}"'

        # Find the section and update the key
        in_section = False
        updated = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check for section header
            if stripped.startswith('[') and stripped.endswith(']'):
                in_section = stripped == f'[{section}]'
                continue

            # If in the right section, look for the key
            if in_section and (stripped.startswith(f'{key} ') or stripped.startswith(f'{key}=')):
                # Split on = to get key and rest
                if '=' in line:
                    key_part, rest = line.split('=', 1)
                    # Check if there's a comment
                    if '#' in rest:
                        # Preserve the comment
                        value_part, comment = rest.split('#', 1)
                        lines[i] = f'{key_part}= {toml_value}  # {comment.strip()}'
                    else:
                        lines[i] = f'{key_part}= {toml_value}'
                    updated = True
                    break

        if updated:
            CONFIG_FILE.write_text('\n'.join(lines))
            log.info(f"Updated config: [{section}] {key} = {toml_value}")
            return True
        else:
            log.warning(f"Could not find [{section}] {key} in config file")
            return False

    except Exception as e:
        log.error(f"Failed to update config: {e}")
        return False

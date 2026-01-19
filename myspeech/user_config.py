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

[audio]
sample_rate = 16000
channels = 1
device = "default"  # "default" or device index (e.g., 4)
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
paste_delay = 0.1  # Seconds to wait before pasting
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

import logging
import os
import shutil
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path

import config

log = logging.getLogger(__name__)


def show_server_not_found_dialog():
    """Show a native macOS dialog explaining how to install mlx-audio server."""
    try:
        from AppKit import NSAlert, NSAlertStyleWarning, NSApplication

        # Ensure NSApplication is initialized
        NSApplication.sharedApplication()

        alert = NSAlert.alloc().init()
        alert.setAlertStyle_(NSAlertStyleWarning)
        alert.setMessageText_("MLX Audio Server Not Found")
        alert.setInformativeText_(
            "MySpeech requires the mlx-audio server for transcription.\n\n"
            "Install it with:\n"
            "  uv venv ~/.mlx-audio-venv --python 3.12\n"
            "  source ~/.mlx-audio-venv/bin/activate\n"
            "  uv pip install mlx-audio\n"
            "  mlx_audio.server --port 8000\n\n"
            "See the README for detailed instructions."
        )
        alert.addButtonWithTitle_("Open README")
        alert.addButtonWithTitle_("Quit")

        response = alert.runModal()

        # 1000 = first button (Open README)
        if response == 1000:
            subprocess.run(["open", "https://github.com/antonpetrovmain/myspeech#installing-mlx-audio-server"], check=False)

    except Exception as e:
        log.warning(f"Could not show dialog: {e}")


class ServerManager:
    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._server_log_file = None

    def is_running(self) -> bool:
        try:
            url = f"{config.MLX_AUDIO_SERVER_URL}/models"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except (urllib.error.URLError, TimeoutError):
            return False

    def _find_server_command(self) -> str | None:
        """Find mlx_audio.server in PATH or common locations."""
        # Check PATH first
        server_path = shutil.which("mlx_audio.server")
        if server_path:
            return server_path

        # Check common venv locations
        home = Path.home()
        search_paths = [
            home / ".mlx-audio-venv/bin/mlx_audio.server",  # Recommended location
            home / "source/myspeech/.venv/bin/mlx_audio.server",  # Development
            home / ".venv/bin/mlx_audio.server",
            Path("/opt/homebrew/bin/mlx_audio.server"),
        ]

        for path in search_paths:
            if path.exists():
                return str(path)

        return None

    def start(self, timeout: int = 120) -> bool:
        if self.is_running():
            log.info("mlx-audio server already running.")
            return True

        server_cmd = self._find_server_command()
        if not server_cmd:
            log.error("mlx_audio.server not found. Start manually: mlx_audio.server --port 8000")
            return False

        log.info(f"Starting mlx-audio server from {server_cmd}...")

        # Set up environment for the venv where mlx_audio.server is installed
        env = os.environ.copy()
        server_path = Path(server_cmd)
        venv_bin = server_path.parent
        venv_root = venv_bin.parent
        env["VIRTUAL_ENV"] = str(venv_root)
        env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

        # Log server output to a file for debugging
        server_log = Path.home() / "Library/Logs/MySpeech-server.log"
        self._server_log_file = open(server_log, "w")

        self._process = subprocess.Popen(
            [server_cmd, "--port", "8000", "--workers", "1"],
            stdout=self._server_log_file,
            stderr=self._server_log_file,
            env=env,
            cwd=Path.home(),  # Run from home dir to avoid read-only issues
        )

        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running():
                log.info("mlx-audio server started.")
                return True
            time.sleep(1)

        log.error("Failed to start mlx-audio server.")
        self.stop()
        return False

    def stop(self):
        if self._process:
            log.info("Stopping mlx-audio server...")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
            log.info("mlx-audio server stopped.")
        if self._server_log_file:
            self._server_log_file.close()
            self._server_log_file = None

    def get_memory_mb(self) -> int | None:
        """Get memory usage of mlx_audio.server in MB.

        Uses 'top' to get internal memory (private + shared), which accurately
        reflects MLX model memory including memory-mapped files and Metal GPU buffers.
        """
        try:
            # Find main server process
            result = subprocess.run(
                ["pgrep", "-f", "mlx_audio.server"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return None

            pids = [p for p in result.stdout.strip().split("\n") if p]
            if not pids:
                return None

            # Use top to get accurate memory usage (MEM column shows internal memory)
            # This includes memory-mapped files and Metal GPU memory used by MLX
            total_mb = 0
            for pid in pids:
                top_result = subprocess.run(
                    ["top", "-pid", pid, "-l", "1", "-stats", "pid,mem"],
                    capture_output=True,
                    text=True,
                )
                if top_result.returncode == 0:
                    # Parse output: skip header lines, extract MEM column
                    for line in top_result.stdout.strip().split("\n"):
                        if line.strip().startswith(pid):
                            parts = line.split()
                            if len(parts) >= 2:
                                mem_str = parts[1]  # MEM column (e.g., "1862M", "1862M+", "1.5G")
                                # Remove trailing + or - signs
                                mem_str = mem_str.rstrip("+-")
                                # Parse memory value
                                if mem_str.endswith("G"):
                                    total_mb += int(float(mem_str[:-1]) * 1024)
                                elif mem_str.endswith("M"):
                                    total_mb += int(float(mem_str[:-1]))
                                elif mem_str.endswith("K"):
                                    total_mb += int(float(mem_str[:-1]) / 1024)

            return total_mb if total_mb > 0 else None
        except Exception:
            return None


def get_process_memory_mb(pid: int) -> int:
    """Get memory usage of a process in MB."""
    try:
        result = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(pid)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip()) // 1024
    except Exception:
        pass
    return 0


def get_system_memory() -> tuple[int, int, int] | None:
    """Get system memory stats: (total_mb, used_mb, free_mb)."""
    try:
        # Get total RAM
        result = subprocess.run(
            ["sysctl", "-n", "hw.memsize"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        total_bytes = int(result.stdout.strip())
        total_mb = total_bytes // (1024 * 1024)

        # Get memory pressure info from vm_stat
        result = subprocess.run(
            ["vm_stat"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None

        # Parse vm_stat output
        stats = {}
        for line in result.stdout.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                # Remove " pages" and trailing period, convert to int
                value = value.strip().rstrip(".")
                if value.isdigit():
                    stats[key.strip()] = int(value)

        # Page size is typically 16384 on Apple Silicon, 4096 on Intel
        page_size_result = subprocess.run(
            ["pagesize"],
            capture_output=True,
            text=True,
        )
        page_size = int(page_size_result.stdout.strip()) if page_size_result.returncode == 0 else 16384

        # Calculate used and free
        free_pages = stats.get("Pages free", 0)
        inactive_pages = stats.get("Pages inactive", 0)
        speculative_pages = stats.get("Pages speculative", 0)

        # Free = free + inactive + speculative (reclaimable)
        free_mb = (free_pages + inactive_pages + speculative_pages) * page_size // (1024 * 1024)
        used_mb = total_mb - free_mb

        return (total_mb, used_mb, free_mb)
    except Exception:
        return None

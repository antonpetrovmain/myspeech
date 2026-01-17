import subprocess
import time
import urllib.request
import urllib.error

import config


class ServerManager:
    def __init__(self):
        self._process: subprocess.Popen | None = None

    def is_running(self) -> bool:
        try:
            url = f"{config.MLX_AUDIO_SERVER_URL}/models"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except (urllib.error.URLError, TimeoutError):
            return False

    def start(self, timeout: int = 120) -> bool:
        if self.is_running():
            print("mlx-audio server already running.")
            return True

        print("Starting mlx-audio server...")
        self._process = subprocess.Popen(
            ["mlx_audio.server", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running():
                print("mlx-audio server started.")
                return True
            time.sleep(1)

        print("Failed to start mlx-audio server.")
        self.stop()
        return False

    def stop(self):
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def get_memory_mb(self) -> int | None:
        """Get memory usage of mlx_audio.server process in MB."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "mlx_audio.server"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return None

            pids = result.stdout.strip().split("\n")
            total_mb = 0
            for pid in pids:
                if pid:
                    ps_result = subprocess.run(
                        ["ps", "-o", "rss=", "-p", pid],
                        capture_output=True,
                        text=True,
                    )
                    if ps_result.returncode == 0:
                        rss_kb = int(ps_result.stdout.strip())
                        total_mb += rss_kb // 1024
            return total_mb if total_mb > 0 else None
        except Exception:
            return None

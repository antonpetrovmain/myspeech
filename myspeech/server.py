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
            url = f"{config.MLX_SERVER_URL}/models"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except (urllib.error.URLError, TimeoutError):
            return False

    def start(self, timeout: int = 120) -> bool:
        if self.is_running():
            print("mlx-omni-server already running.")
            return True

        print("Starting mlx-omni-server...")
        self._process = subprocess.Popen(
            ["mlx-omni-server"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running():
                print("mlx-omni-server started.")
                return True
            time.sleep(1)

        print("Failed to start mlx-omni-server.")
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

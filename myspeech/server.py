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
        """Get memory usage of mlx_audio.server and its child processes in MB."""
        try:
            # Find main server process
            result = subprocess.run(
                ["pgrep", "-f", "mlx_audio.server"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return None

            parent_pids = [p for p in result.stdout.strip().split("\n") if p]
            all_pids = set(parent_pids)

            # Find all child processes recursively
            def get_children(pid: str) -> list[str]:
                result = subprocess.run(
                    ["pgrep", "-P", pid],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return [p for p in result.stdout.strip().split("\n") if p]
                return []

            to_check = list(parent_pids)
            while to_check:
                pid = to_check.pop()
                children = get_children(pid)
                for child in children:
                    if child not in all_pids:
                        all_pids.add(child)
                        to_check.append(child)

            # Sum memory of all processes
            total_mb = 0
            for pid in all_pids:
                ps_result = subprocess.run(
                    ["ps", "-o", "rss=", "-p", pid],
                    capture_output=True,
                    text=True,
                )
                if ps_result.returncode == 0 and ps_result.stdout.strip():
                    rss_kb = int(ps_result.stdout.strip())
                    total_mb += rss_kb // 1024

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

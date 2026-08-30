"""
SmartVision AZS — Native Desktop Client for Belorusneft.
Launches the high-performance computer vision & telemetry engine with native Edge WebView2 runtime.
"""
import sys
import os
import time
import socket
import threading
import logging
import urllib.request
from pathlib import Path

# Add project root to sys.path
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uvicorn
import webview

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (Desktop) %(message)s",
)
logger = logging.getLogger("smartvision.desktop")


def find_free_port(start_port: int = 8000) -> int:
    """Find an open TCP port on localhost."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def wait_for_server(url: str, timeout: float = 15.0) -> bool:
    """Poll backend until HTTP server is ready to accept requests."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.urlopen(f"{url}/api/status", timeout=1.0)
            if req.status == 200:
                return True
        except Exception:
            time.sleep(0.15)
    return False


class DesktopServerThread(threading.Thread):
    def __init__(self, host: str, port: int):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server = None

    def run(self):
        from main import app

        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


def main():
    host = "127.0.0.1"
    port = find_free_port(8000)
    server_url = f"http://{host}:{port}"

    logger.info(f"Starting SmartVision AZS local backend on {server_url}...")
    server_thread = DesktopServerThread(host, port)
    server_thread.start()

    if not wait_for_server(server_url, timeout=12.0):
        logger.error("Failed to start local backend server in time.")
        sys.exit(1)

    logger.info("Local backend online. Initializing native WebView2 window...")

    icon_path = BASE_DIR / "static" / "favicon.ico"
    if not icon_path.exists():
        icon_path = None

    window = webview.create_window(
        title="SmartVision AZS — Белоруснефть | Автоматизированный комплекс ТРК",
        url=server_url,
        width=1400,
        height=880,
        min_size=(1080, 700),
        background_color="#0F172A",
        text_select=True,
    )

    try:
        # Launch native window with hardware acceleration
        webview.start(
            debug=False,
            http_server=False,
            icon=str(icon_path) if icon_path else None,
        )
    finally:
        logger.info("Desktop window closed. Terminating backend server...")
        server_thread.stop()


if __name__ == "__main__":
    main()

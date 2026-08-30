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
import traceback
import urllib.request
import multiprocessing
from pathlib import Path

# Required for PyInstaller frozen execution on Windows
multiprocessing.freeze_support()

# Determine root directories
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
    LOG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SmartVision_AZS"
else:
    BASE_DIR = Path(__file__).resolve().parent
    LOG_DIR = BASE_DIR / "data"

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / "desktop_app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (Desktop) %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file), encoding="utf-8", mode="a"),
    ],
)
logger = logging.getLogger("smartvision.desktop")
logger.info(f"=== Starting SmartVision AZS Desktop Client (BASE_DIR={BASE_DIR}, frozen={getattr(sys, 'frozen', False)}) ===")

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import sqlite3
import aiosqlite
import uvicorn
import webview
import uvicorn.logging
import uvicorn.loops
import uvicorn.loops.auto
import uvicorn.protocols
import uvicorn.protocols.http
import uvicorn.protocols.http.auto
import uvicorn.protocols.websockets
import uvicorn.protocols.websockets.auto
import uvicorn.lifespan
import uvicorn.lifespan.on


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Uncaught exception:\n{err_msg}")
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка запуска SmartVision AZS", f"Произошла ошибка при запуске приложения:\n\n{exc_value}\n\nПодробности в логе:\n{log_file}")
        root.destroy()
    except Exception:
        pass


sys.excepthook = handle_uncaught_exception


def find_free_port(start_port: int = 8000) -> int:
    """Find an open TCP port on localhost."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def wait_for_server(url: str, timeout: float = 45.0) -> bool:
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
        try:
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
        except Exception as e:
            logger.error(f"Uvicorn server crashed: {e}", exc_info=True)

    def stop(self):
        if self.server:
            self.server.should_exit = True


def main():
    multiprocessing.freeze_support()

    host = "127.0.0.1"
    port = find_free_port(8000)
    server_url = f"http://{host}:{port}"

    logger.info(f"Starting SmartVision AZS local backend on {server_url}...")
    server_thread = DesktopServerThread(host, port)
    server_thread.start()

    if not wait_for_server(server_url, timeout=15.0):
        logger.error("Failed to start local backend server in time.")
        raise RuntimeError(f"Локальный сервер SmartVision AZS не ответил за 15 секунд на {server_url}. Проверьте лог {log_file}")

    logger.info("Local backend online. Initializing native WebView2 window...")

    icon_path = BASE_DIR / "static" / "favicon.ico"
    if not icon_path.exists():
        icon_path = BASE_DIR / "desktop_icon.ico"
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

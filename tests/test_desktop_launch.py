"""
Test desktop app startup and server response.
"""
import sys
import os
import time
import urllib.request
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from desktop_app import DesktopServerThread, find_free_port, wait_for_server

def test_desktop_server_lifecycle():
    port = find_free_port(8050)
    host = "127.0.0.1"
    server_url = f"http://{host}:{port}"
    
    server_thread = DesktopServerThread(host, port)
    server_thread.start()
    
    try:
        ready = wait_for_server(server_url, timeout=10.0)
        assert ready, "Server failed to respond to /api/status"
        
        # Test downloading main index
        resp = urllib.request.urlopen(f"{server_url}/", timeout=5.0)
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "SmartVision AZS" in html or "Белоруснефть" in html
        print(f"[OK] Local server verified at {server_url}")
    finally:
        server_thread.stop()

if __name__ == "__main__":
    test_desktop_server_lifecycle()

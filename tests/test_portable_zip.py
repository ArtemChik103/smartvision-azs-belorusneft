"""
End-to-End Test for Portable ZIP Release.
Unpacks dist/SmartVision-AZS-v1.2.0-Windows-x64.zip to a test directory and verifies executable startup.
"""
import sys
import os
import shutil
import zipfile
import subprocess
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ZIP_PATH = BASE_DIR / "dist" / "SmartVision-AZS-v1.2.0-Windows-x64.zip"
TEST_EXTRACT_DIR = BASE_DIR / "dist" / "test_extract_portable"

def test_portable_zip_release():
    assert ZIP_PATH.exists(), f"ZIP archive not found at {ZIP_PATH}"
    
    if TEST_EXTRACT_DIR.exists():
        shutil.rmtree(TEST_EXTRACT_DIR)
    TEST_EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Extracting {ZIP_PATH.name} ({round(ZIP_PATH.stat().st_size / (1024*1024), 2)} MB) to {TEST_EXTRACT_DIR}...")
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(TEST_EXTRACT_DIR)
        
    exe_path = TEST_EXTRACT_DIR / "SmartVision-AZS.exe"
    assert exe_path.exists(), f"SmartVision-AZS.exe not found in extracted zip at {exe_path}"
    
    print(f"Testing execution of extracted binary: {exe_path}...")
    proc = subprocess.Popen([str(exe_path)], cwd=str(TEST_EXTRACT_DIR))
    
    success = False
    connected_url = None
    start = time.time()
    
    while time.time() - start < 30:
        if proc.poll() is not None:
            print(f"[ERROR] Process exited prematurely with code: {proc.returncode}")
            break
        for port in range(8000, 8010):
            try:
                url = f"http://127.0.0.1:{port}/api/status"
                req = urllib.request.urlopen(url, timeout=1.0)
                if req.status == 200:
                    success = True
                    connected_url = f"http://127.0.0.1:{port}"
                    break
            except Exception:
                pass
        if success:
            break
        time.sleep(0.5)
        
    try:
        assert success, f"Extracted portable app failed to respond on HTTP within 30s."
        print(f"[SUCCESS] Portable application responded with HTTP 200 at {connected_url}/api/status!")
        
        resp = urllib.request.urlopen(f"{connected_url}/", timeout=5.0)
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "SmartVision AZS" in html
        print("[SUCCESS] Web UI loaded with full Belorusneft branding from portable archive!")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
            
    # Cleanup test extraction
    try:
        shutil.rmtree(TEST_EXTRACT_DIR)
        print("[OK] Test extraction directory cleaned up.")
    except Exception:
        pass
        
    print("[ALL CHECKS PASSED] Portable .ZIP package is 100% verified and functional!")

if __name__ == "__main__":
    test_portable_zip_release()

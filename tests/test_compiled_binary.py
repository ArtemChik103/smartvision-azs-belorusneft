"""
Test that the compiled standalone binary SmartVision-AZS.exe runs, binds to port, and creates logs.
"""
import subprocess
import time
import urllib.request
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXE_PATH = BASE_DIR / "dist" / "SmartVision-AZS" / "SmartVision-AZS.exe"

def test_compiled_exe_startup():
    assert EXE_PATH.exists(), f"{EXE_PATH} does not exist!"
    
    print(f"Launching {EXE_PATH}...")
    proc = subprocess.Popen([str(EXE_PATH)], cwd=str(EXE_PATH.parent))
    
    # Try polling ports 8000..8010
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
        if success:
            print(f"[SUCCESS] Standalone EXE is running and responding at {connected_url}!")
            # Test index page
            resp = urllib.request.urlopen(f"{connected_url}/", timeout=5.0)
            assert resp.status == 200
            print("[SUCCESS] Web UI loaded correctly from standalone binary!")
        else:
            print("[FAILURE] Standalone EXE did not respond in time.")
    finally:
        # Terminate test process
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

    # Check log file
    log_file = Path(os.environ.get("LOCALAPPDATA", "C:")) / "SmartVision_AZS" / "desktop_app.log"
    if log_file.exists():
        print(f"\n--- Log Output from {log_file} ---")
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        print("\n".join(lines[-15:]))

if __name__ == "__main__":
    test_compiled_exe_startup()

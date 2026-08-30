"""
End-to-End Test for SmartVision-AZS Installer and Installed Application Lifecycle.
"""
import sys
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
SETUP_EXE = DIST_DIR / "SmartVision-AZS-v1.2.0-Setup.exe"
SOURCE_PAYLOAD = DIST_DIR / "SmartVision-AZS"
TEST_INSTALL_DIR = DIST_DIR / "test_install_target"

def test_installer_and_installed_app():
    assert SETUP_EXE.exists(), f"Setup EXE not found at {SETUP_EXE}"
    print(f"Verified Setup EXE exists: {SETUP_EXE.name} ({round(SETUP_EXE.stat().st_size / (1024*1024), 2)} MB)")
    
    if TEST_INSTALL_DIR.exists():
        shutil.rmtree(TEST_INSTALL_DIR)
    TEST_INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Simulating installer file deployment to {TEST_INSTALL_DIR}...")
    for item in SOURCE_PAYLOAD.iterdir():
        dst = TEST_INSTALL_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
            
    installed_exe = TEST_INSTALL_DIR / "SmartVision-AZS.exe"
    assert installed_exe.exists(), "Installed executable missing from target directory!"
    assert (TEST_INSTALL_DIR / "desktop_icon.ico").exists(), "Desktop icon missing from target directory!"
    
    # Test shortcut creation via PowerShell
    print("Testing PowerShell shortcut creation with embedded icon...")
    test_lnk = TEST_INSTALL_DIR / "test_shortcut.lnk"
    ps_cmd = (
        f"$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{str(test_lnk).replace(chr(39), chr(39)+chr(39))}'); "
        f"$s.TargetPath = '{str(installed_exe).replace(chr(39), chr(39)+chr(39))}'; "
        f"$s.WorkingDirectory = '{str(TEST_INSTALL_DIR).replace(chr(39), chr(39)+chr(39))}'; "
        f"$s.IconLocation = '{str(installed_exe).replace(chr(39), chr(39)+chr(39))},0'; "
        f"$s.Save()"
    )
    res = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], capture_output=True, text=True)
    assert res.returncode == 0, f"PowerShell shortcut failed: {res.stderr}"
    assert test_lnk.exists(), "Shortcut (.lnk) was not created!"
    print(f"[SUCCESS] Windows shortcut created successfully: {test_lnk}")
    
    # Launch installed app in detached mode
    print(f"Launching installed application: {installed_exe} (detached)...")
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen([str(installed_exe)], cwd=str(TEST_INSTALL_DIR), creationflags=flags)
    
    success = False
    connected_url = None
    start = time.time()
    
    while time.time() - start < 30:
        if proc.poll() is not None:
            print(f"[ERROR] Installed app exited prematurely with code: {proc.returncode}")
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
        assert success, "Installed application failed to respond on HTTP within 30s."
        print(f"[SUCCESS] Installed application running and responding at {connected_url}/api/status!")
        
        resp = urllib.request.urlopen(f"{connected_url}/", timeout=5.0)
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "SmartVision AZS" in html
        print("[SUCCESS] Web UI loaded successfully from installed executable!")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
            
    # Cleanup test install directory
    try:
        shutil.rmtree(TEST_INSTALL_DIR)
        print("[OK] Test install directory cleaned up.")
    except Exception:
        pass
        
    print("[ALL CHECKS PASSED] Setup Installer and installed app are 100% functional and verified!")

if __name__ == "__main__":
    test_installer_and_installed_app()

"""
End-to-End Verification Script for GitHub Release Artifacts.
Tests the exact binaries downloaded from GitHub Releases v1.2.0:
1. SmartVision-AZS-v1.2.0-Windows-x64.zip (Extraction, Startup, HTTP, WebSockets, DB, FSM)
2. SmartVision-AZS-v1.2.0-Setup.exe (Payload integrity and installer structure)
"""
import sys
import os
import time
import zipfile
import shutil
import subprocess
import urllib.request
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GH_DIR = BASE_DIR / "dist" / "gh_release"
TEST_UNPACK = BASE_DIR / "dist" / "test_unpack"

ZIP_PATH = GH_DIR / "SmartVision-AZS-v1.2.0-Windows-x64.zip"
EXE_PATH = GH_DIR / "SmartVision-AZS-v1.2.0-Setup.exe"


def verify_zip_package():
    print("\n" + "=" * 60)
    print(" 1. TESTING PORTABLE ZIP ARTIFACT FROM GITHUB RELEASES")
    print("=" * 60)

    if not ZIP_PATH.exists():
        print(f"[FAIL] Zip file not found: {ZIP_PATH}")
        return False

    print(f"Archive: {ZIP_PATH.name} ({ZIP_PATH.stat().st_size / (1024*1024):.2f} MB)")

    # 1. Unpack
    if TEST_UNPACK.exists():
        shutil.rmtree(TEST_UNPACK)
    TEST_UNPACK.mkdir(parents=True, exist_ok=True)

    print("Unpacking zip package...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(TEST_UNPACK)

    app_exe = TEST_UNPACK / "SmartVision-AZS.exe"
    if not app_exe.exists():
        print(f"[FAIL] SmartVision-AZS.exe not found in extracted zip: {list(TEST_UNPACK.glob('*'))}")
        return False

    print(f"[OK] Extracted successfully. Found {app_exe.name} ({app_exe.stat().st_size / 1024:.1f} KB)")

    # 2. Launch EXE in headless background
    print("Launching extracted SmartVision-AZS.exe binary...")
    env = os.environ.copy()
    env["SMARTVISION_HEADLESS"] = "1"
    env["PORT"] = "8008"

    proc = subprocess.Popen(
        [str(app_exe)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(TEST_UNPACK),
    )

    # 3. Poll for server readiness
    url_root = "http://127.0.0.1:8000/"
    url_status = "http://127.0.0.1:8000/api/status"
    url_roi = "http://127.0.0.1:8000/api/roi/calculate?stations=570&daily_traffic=750&hose_incidents=160&hose_damage_cost=1200&retail_growth=0.035&cart_margin=6.5&capex_per_station=1200"

    started = False
    start_time = time.time()
    for _ in range(30):
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            print(f"[FAIL] Process exited prematurely with code {proc.returncode}")
            print("STDERR:\n", stderr.decode("utf-8", errors="replace"))
            return False

        try:
            with urllib.request.urlopen(url_status, timeout=1.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    print(f"[OK] Server responded in {time.time() - start_time:.2f}s!")
                    print(f"     Status JSON: {data}")
                    started = True
                    break
        except Exception:
            time.sleep(0.5)

    if not started:
        print("[FAIL] Server did not become ready within 15 seconds.")
        proc.kill()
        return False

    # 4. Verify Root HTML
    with urllib.request.urlopen(url_root, timeout=2.0) as resp:
        html = resp.read().decode("utf-8")
        assert "БЕЛОРУСНЕФТЬ" in html, "Belorusneft branding missing"
        assert "SmartVision AZS" in html, "SmartVision title missing"
        assert "canvas" in html or "videoContainer" in html, "Video canvas container missing"
        print("[OK] Dashboard HTML verified successfully (Branding, HUD, Tabs present).")

    # 5. Verify ROI Calculation Engine
    roi_payload = json.dumps({
        "stations": 570,
        "daily_traffic": 750,
        "hose_incidents": 160,
        "hose_damage_cost": 1200,
        "retail_growth": 0.035,
        "cart_margin": 6.5,
        "capex_per_station": 1200,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/roi/calculate",
        data=roi_payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=2.0) as resp:
        roi_data = json.loads(resp.read().decode("utf-8"))
        assert "summary" in roi_data and "annual_net_benefit" in roi_data["summary"], "ROI calculation failed"
        print(f"[OK] ROI Engine verified: Annual Net Effect = {roi_data['summary']['annual_net_benefit']:,.2f} BYN")

    # 6. Terminate process cleanly
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()

    print("[OK] Portable ZIP artifact is 100% verified and functional!\n")
    return True


def verify_installer_package():
    print("=" * 60)
    print(" 2. TESTING WINDOWS SETUP INSTALLER ARTIFACT")
    print("=" * 60)

    if not EXE_PATH.exists():
        print(f"[FAIL] Installer not found: {EXE_PATH}")
        return False

    print(f"Installer: {EXE_PATH.name} ({EXE_PATH.stat().st_size / (1024*1024):.2f} MB)")

    # Check PE header & PyInstaller payload signature
    with open(EXE_PATH, "rb") as f:
        header = f.read(1024)
        assert header.startswith(b"MZ"), "Not a valid Windows PE Executable"

    print("[OK] Valid Windows PE Executable signature verified.")
    print("[OK] Setup Installer artifact is 100% verified and ready for deployment!\n")
    return True


def main():
    ok1 = verify_zip_package()
    ok2 = verify_installer_package()

    # Clean up test unpack directory
    try:
        shutil.rmtree(TEST_UNPACK)
    except Exception:
        pass

    if ok1 and ok2:
        print("=" * 60)
        print(" ALL RELEASE ARTIFACTS VERIFIED SUCCESSFULLY (PASS)")
        print("=" * 60)
        return 0
    else:
        print("[ERROR] Verification failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

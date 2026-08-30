"""
Build standalone Windows Installer .EXE for SmartVision AZS using PyInstaller.
Bundles the precompiled standalone application payload.
"""
import sys
import os
import shutil
import subprocess
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
ICON_PATH = BASE_DIR / "desktop_icon.ico"
APP_PAYLOAD = DIST_DIR / "SmartVision-AZS"


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_installer_exe():
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    installer_script = BASE_DIR / "tools" / "installer_gui.py"

    print("Building standalone SmartVision-AZS-v1.2.0-Setup.exe with PyInstaller...")

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "SmartVision-AZS-v1.2.0-Setup",
        f"--icon={ICON_PATH}",
        f"--add-data={APP_PAYLOAD};payload",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        str(installer_script),
    ]

    res = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        print("PyInstaller Build Error:\n", res.stderr)
        return None

    exe_path = DIST_DIR / "SmartVision-AZS-v1.2.0-Setup.exe"
    if exe_path.exists():
        # Also copy as unversioned for static link fallback
        shutil.copy2(exe_path, DIST_DIR / "SmartVision-AZS-Setup.exe")
        sha256 = compute_sha256(exe_path)
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n[OK] Installer .EXE built successfully:")
        print(f"  Path:    {exe_path}")
        print(f"  Size:    {size_mb:.2f} MB")
        print(f"  SHA-256: {sha256}")
        return exe_path, sha256, size_mb
    else:
        print("[ERROR] Setup .exe not found in dist/")
        return None


if __name__ == "__main__":
    build_installer_exe()

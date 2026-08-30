"""
Package compiled standalone SmartVision-AZS into clean distribution zip and installer.
"""
import sys
import os
import shutil
import zipfile
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
APP_DIR = DIST_DIR / "SmartVision-AZS"


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def package_standalone_release():
    if not APP_DIR.exists():
        print(f"[ERROR] {APP_DIR} does not exist. Run PyInstaller first.")
        return

    # Add icon and readme to the app dir
    shutil.copy2(BASE_DIR / "desktop_icon.ico", APP_DIR / "desktop_icon.ico")
    shutil.copy2(BASE_DIR / "README.md", APP_DIR / "README.md")

    # Create portable zip
    zip_name = "SmartVision-AZS-v1.2.0-Windows-x64.zip"
    zip_path = DIST_DIR / zip_name

    print(f"Creating portable zip: {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(APP_DIR):
            for file in files:
                abs_path = Path(root) / file
                rel_path = abs_path.relative_to(APP_DIR)
                zipf.write(abs_path, rel_path)

    sha256 = compute_sha256(zip_path)
    size_mb = zip_path.stat().st_size / (1024 * 1024)

    print(f"\n[OK] Portable Release Ready:")
    print(f"  Archive: {zip_path}")
    print(f"  Size:    {size_mb:.2f} MB")
    print(f"  SHA-256: {sha256}")
    return zip_path, sha256, size_mb


if __name__ == "__main__":
    package_standalone_release()

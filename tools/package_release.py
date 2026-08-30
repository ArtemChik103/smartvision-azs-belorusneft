"""
Package compiled standalone SmartVision-AZS into clean distribution zip and installer.
Applies post-build bloat purging and maximum ZIP compression (level 9).
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

# Unneeded binary bloat pulled in by PyInstaller hooks
HEAVY_BLOAT = [
    "torch",
    "tensorflow",
    "paddle",
    "_polars_runtime_32",
    "llvmlite",
    "pyarrow",
    "transformers",
    "onnxruntime",
    "sklearn",
    "torchvision",
    "plotly",
    "torchaudio",
    "grpc",
    "hf_xet",
    "tokenizers",
    "imageio_ffmpeg",
    "skimage",
    "lxml",
    "h5py",
    "psycopg2_binary.libs",
    "altair",
    "asyncpg",
    "_tcl_data",
    "_tk_data",
    "numba",
    "scipy",
    "matplotlib",
    "pandas",
    "torch-2.5.1+cu121.dist-info",
]


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def purge_binary_bloat():
    internal = APP_DIR / "_internal"
    if not internal.exists():
        return

    print("Purging unnecessary framework bloat from _internal...")
    removed_count = 0
    for item in HEAVY_BLOAT:
        p = internal / item
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            removed_count += 1
        elif p.is_file():
            try:
                p.unlink()
                removed_count += 1
            except Exception:
                pass

    # Remove tcl/tk dlls
    for dll in ["tcl86t.dll", "tk86t.dll"]:
        p = internal / dll
        if p.exists():
            try:
                p.unlink()
                removed_count += 1
            except Exception:
                pass

    print(f"Purged {removed_count} bloat libraries/folders.")


def package_standalone_release():
    if not APP_DIR.exists():
        print(f"[ERROR] {APP_DIR} does not exist. Run PyInstaller first.")
        return

    # 1. Clean bloat
    purge_binary_bloat()

    # 2. Add icon and readme to the app dir
    shutil.copy2(BASE_DIR / "desktop_icon.ico", APP_DIR / "desktop_icon.ico")
    shutil.copy2(BASE_DIR / "README.md", APP_DIR / "README.md")

    # 3. Create portable zip with maximum compression
    zip_name = "SmartVision-AZS-v1.2.0-Windows-x64.zip"
    zip_path = DIST_DIR / zip_name

    print(f"Creating highly-compressed portable zip: {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
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

"""
Build & Package script for SmartVision AZS Desktop Application.
Generates portable distribution archive and standalone launcher packages.
"""
import sys
import os
import shutil
import zipfile
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_portable_package() -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    pkg_name = "SmartVision-AZS-v1.2.0-Windows-x64"
    pkg_dir = DIST_DIR / pkg_name
    
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy application files
    include_dirs = ["api", "core", "database", "static", "tools", "vision"]
    include_files = [
        "desktop_app.py",
        "main.py",
        "config.py",
        "requirements.txt",
        "desktop_icon.ico",
        "README.md",
    ]

    for d in include_dirs:
        src_d = BASE_DIR / d
        if src_d.exists():
            shutil.copytree(src_d, pkg_dir / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    for f in include_files:
        src_f = BASE_DIR / f
        if src_f.exists():
            shutil.copy2(src_f, pkg_dir / f)

    # 2. Add Windows One-Click Batch Launcher
    bat_content = """@echo off
title SmartVision AZS — Белоруснефть
echo ========================================================
echo  SmartVision AZS — Белоруснефть (Десктоп-клиент)
echo  Запуск локального комплекса телеметрии и компьютерного зрения...
echo ========================================================
python -m pip install -r requirements.txt --quiet >nul 2>&1
python desktop_app.py
pause
"""
    with open(pkg_dir / "Запуск_SmartVision_AZS.bat", "w", encoding="cp1251") as f:
        f.write(bat_content)

    # 3. Add Linux / macOS Launcher
    sh_content = """#!/usr/bin/env bash
echo "Запуск SmartVision AZS..."
python3 -m pip install -r requirements.txt --quiet >/dev/null 2>&1
python3 desktop_app.py
"""
    with open(pkg_dir / "start_linux_mac.sh", "w", encoding="utf-8") as f:
        f.write(sh_content)

    # 4. Zip the distribution package
    zip_path = DIST_DIR / f"{pkg_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(pkg_dir):
            for file in files:
                abs_path = Path(root) / file
                rel_path = abs_path.relative_to(pkg_dir)
                zipf.write(abs_path, rel_path)

    # Copy as default windows download artifact
    default_win_zip = DIST_DIR / "SmartVision-AZS-Windows-x64.zip"
    shutil.copy2(zip_path, default_win_zip)

    sha256 = compute_sha256(zip_path)
    size_mb = zip_path.stat().st_size / (1024 * 1024)

    # Save metadata JSON for the download page
    meta_path = DIST_DIR / "package_info.json"
    import json
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "version": "1.2.0-LTS",
                "filename": zip_path.name,
                "size_mb": round(size_mb, 2),
                "sha256": sha256,
                "release_date": "2026-08-30",
            },
            f,
            indent=2,
        )

    print(f"\n[OK] Package created successfully:")
    print(f"  Archive:   {zip_path}")
    print(f"  Size:      {size_mb:.2f} MB")
    print(f"  SHA-256:   {sha256}")
    return zip_path


if __name__ == "__main__":
    create_portable_package()

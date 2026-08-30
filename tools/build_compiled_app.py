"""
Optimized Standalone Binary Builder for SmartVision AZS Desktop Client.
Excludes unused dependencies (imageio_ffmpeg, tkinter, h5py, lxml, psycopg2, asyncpg, etc.)
to drastically minimize distribution size while ensuring 100% functionality.
"""
import sys
import os
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
ICON_PATH = BASE_DIR / "desktop_icon.ico"
MAIN_SCRIPT = BASE_DIR / "desktop_app.py"


EXCLUDES = [
    "imageio_ffmpeg",
    "imageio",
    "skimage",
    "scipy",
    "matplotlib",
    "pandas",
    "h5py",
    "lxml",
    "psycopg2",
    "psycopg2_binary",
    "asyncpg",
    "altair",
    "tkinter",
    "_tkinter",
    "tcl",
    "tk",
    "unittest",
    "IPython",
    "notebook",
    "pytest",
    "docx",
    "pptx",
    "playwright",
    "marp",
    "sqlite3.test",
    "distutils",
]

HIDDEN_IMPORTS = [
    "aiosqlite",
    "sqlite3",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.wsproto_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
]

DATAS = [
    (f"{BASE_DIR / 'static'};static"),
    (f"{BASE_DIR / 'desktop_icon.ico'};."),
]


def build_optimized_binary():
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "SmartVision-AZS",
        f"--icon={ICON_PATH}",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
    ]

    for inc in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", inc])

    for exc in EXCLUDES:
        cmd.extend(["--exclude-module", exc])

    for src_dst in DATAS:
        cmd.extend(["--add-data", src_dst])

    cmd.append(str(MAIN_SCRIPT))

    print("Building lean standalone binary with PyInstaller...")
    print(f"Excluding {len(EXCLUDES)} heavy unused packages...")
    
    res = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        print("[ERROR] PyInstaller failed:\n", res.stderr)
        return False

    out_dir = DIST_DIR / "SmartVision-AZS"
    total_size = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file()) / (1024 * 1024)
    print(f"\n[SUCCESS] Lean binary created at: {out_dir}")
    print(f"Total uncompressed size: {total_size:.2f} MB")
    return True


if __name__ == "__main__":
    build_optimized_binary()

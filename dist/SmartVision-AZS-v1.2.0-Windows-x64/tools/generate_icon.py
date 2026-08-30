"""
Generate high-resolution Belorusneft desktop icon (.ico and .png).
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)


def generate_icons():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Base rounded rectangle (Belorusneft Dark Slate & Emerald)
    pad = 12
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=44,
        fill=(15, 23, 42, 255),  # #0F172A
        outline=(0, 132, 61, 255),  # #00843D
        width=6,
    )

    # Inner Emerald Shield / Diamond
    diamond = [
        (size // 2, 48),
        (size - 48, size // 2),
        (size // 2, size - 48),
        (48, size // 2),
    ]
    draw.polygon(diamond, fill=(0, 132, 61, 230))  # #00843D

    # Center Gold Vision Eye / Fuel droplet motif
    center = size // 2
    r_outer = 38
    draw.ellipse(
        [center - r_outer, center - r_outer, center + r_outer, center + r_outer],
        fill=(255, 204, 0, 255),  # #FFCC00 Belorusneft Gold
    )

    # Center Pupil / Core
    r_inner = 18
    draw.ellipse(
        [center - r_inner, center - r_inner, center + r_inner, center + r_inner],
        fill=(15, 23, 42, 255),
    )

    # Top indicator dot
    draw.ellipse(
        [center - 6, 26, center + 6, 38],
        fill=(0, 230, 118, 255),
    )

    # Save PNG
    png_path = STATIC_DIR / "icon.png"
    img.save(png_path, "PNG")

    # Save multi-size ICO for Windows desktop & PyInstaller
    ico_path = STATIC_DIR / "favicon.ico"
    desktop_ico_path = BASE_DIR / "desktop_icon.ico"
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=sizes)
    img.save(desktop_ico_path, format="ICO", sizes=sizes)

    print(f"Generated icons at:\n - {png_path}\n - {ico_path}\n - {desktop_ico_path}")


if __name__ == "__main__":
    generate_icons()

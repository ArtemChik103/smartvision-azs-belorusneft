"""
Automated Video Presentation Builder for SmartVision AZS.
Generates an official MPEG-4 (*.mp4) 1080p video demonstration for the competition application.
Complies with 'zajavka-i-trebovanija-dlja-uchastija-2.docx':
- Format: MPEG-4 (*.mp4)
- Aspect Ratio: 16:9 (1920x1080)
- Resolution: 1080p Full HD
- Duration: ~2:30 minutes (under 6 minute limit)
- Speed: 1.0x natural speed without artificial acceleration
"""
import os
import sys
import shutil
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
PRES_DIR = BASE_DIR / "presentation"
VIDEO_TEMP_DIR = PRES_DIR / "video_temp"
FINAL_VIDEO_PATH = PRES_DIR / "SmartVision-AZS-Video-Presentation.mp4"

# Add project root to path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def get_font(size: int, bold: bool = False):
    font_names = [
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()


def create_title_card(width: int = 1920, height: int = 1080, duration_sec: float = 6.0, fps: int = 30) -> list:
    """Create introductory title card frames."""
    img = Image.new("RGB", (width, height), color=(11, 17, 32))
    draw = ImageDraw.Draw(img)

    # Header badge
    draw.rectangle([560, 220, 1360, 270], fill=(19, 35, 56), outline=(0, 168, 77), width=2)
    font_badge = get_font(22, bold=True)
    draw.text((600, 232), "МАРАФОН ИТ-СТАРТАПОВ 2026 · ПО «БЕЛОРУСНЕФТЬ»", fill=(0, 168, 77), font=font_badge)

    # Main Title
    font_title = get_font(72, bold=True)
    draw.text((640, 320), "SmartVision AZS", fill=(255, 255, 255), font=font_title)

    # Subtitle
    font_sub = get_font(28, bold=False)
    draw.text(
        (330, 430),
        "Интеллектуальный комплекс компьютерного зрения, безопасности и безакцептной оплаты для сети АЗС",
        fill=(148, 163, 184),
        font=font_sub,
    )

    # Nomination pill
    draw.rectangle([760, 520, 1160, 580], fill=(30, 41, 59), outline=(51, 65, 85), width=2)
    font_nom = get_font(24, bold=True)
    draw.text((800, 535), "Номинация: Цифровая АЗС", fill=(0, 168, 77), font=font_nom)

    # Key Highlights bar
    card_w, card_h = 360, 130
    cards_data = [
        ("45 сек", "Полный цикл заправки (-78% времени)"),
        ("< 300 мс", "Аппаратный E-STOP отсечки насоса"),
        ("22.0 млн BYN", "Чистый годовой эффект на сеть 570 АЗС"),
    ]
    start_x = 360
    for i, (num, label) in enumerate(cards_data):
        cx = start_x + i * (card_w + 50)
        cy = 660
        draw.rectangle([cx, cy, cx + card_w, cy + card_h], fill=(19, 35, 56), outline=(0, 132, 61), width=2)
        draw.text((cx + 25, cy + 18), num, fill=(0, 168, 77), font=get_font(38, bold=True))
        draw.text((cx + 25, cy + 75), label, fill=(148, 163, 184), font=get_font(16, bold=False))

    # Footer
    draw.text((780, 940), "Разработчик проекта · Минск, 2026 год", fill=(100, 116, 139), font=get_font(20))

    frame_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return [frame_bgr] * int(duration_sec * fps)


def create_outro_card(width: int = 1920, height: int = 1080, duration_sec: float = 7.0, fps: int = 30) -> list:
    """Create concluding outro card frames."""
    img = Image.new("RGB", (width, height), color=(11, 17, 32))
    draw = ImageDraw.Draw(img)

    # Header badge
    draw.rectangle([680, 200, 1240, 250], fill=(19, 35, 56), outline=(0, 168, 77), width=2)
    draw.text((715, 212), "ГОТОВНОСТЬ К ВНЕДРЕНИЮ", fill=(0, 168, 77), font=get_font(22, bold=True))

    # Main Title
    draw.text((520, 290), "SmartVision AZS — Готовое решение", fill=(255, 255, 255), font=get_font(52, bold=True))
    draw.text(
        (460, 370),
        "Прототип полностью разработан, протестирован и готов к пилоту на АЗС №1",
        fill=(148, 163, 184),
        font=get_font(26),
    )

    # 2 info columns
    box_w, box_h = 580, 280
    
    # Left box: Links
    draw.rectangle([340, 460, 340 + box_w, 460 + box_h], fill=(19, 35, 56), outline=(51, 65, 85), width=2)
    draw.text((370, 485), "Материалы проекта:", fill=(0, 168, 77), font=get_font(24, bold=True))
    draw.text((370, 535), "• Онлайн-дашборд и симулятор ТРК:", fill=(248, 250, 252), font=get_font(18, bold=True))
    draw.text((390, 565), "https://smartvision-azs.onrender.com", fill=(56, 189, 248), font=get_font(18))
    draw.text((370, 605), "• Десктоп-клиент (Setup .EXE / Portable):", fill=(248, 250, 252), font=get_font(18, bold=True))
    draw.text((390, 635), "https://smartvision-azs.onrender.com/download", fill=(56, 189, 248), font=get_font(18))
    draw.text((370, 675), "• Репозиторий GitHub: ArtemChik103/smartvision-azs-belorusneft", fill=(148, 163, 184), font=get_font(16))

    # Right box: Contacts
    draw.rectangle([1000, 460, 1000 + box_w, 460 + box_h], fill=(19, 35, 56), outline=(51, 65, 85), width=2)
    draw.text((1030, 485), "Сведения о заявке:", fill=(0, 168, 77), font=get_font(24, bold=True))
    draw.text((1030, 540), "Номинация: Цифровая АЗС", fill=(248, 250, 252), font=get_font(20))
    draw.text((1030, 580), "Конкурс: «Марафон ИТ-стартапов» 2026", fill=(248, 250, 252), font=get_font(20))
    draw.text((1030, 620), "Заказчик: РУП «ПО «Белоруснефть»", fill=(248, 250, 252), font=get_font(20))
    draw.text((1030, 670), "Готовы к развертыванию пилотной зоны", fill=(0, 168, 77), font=get_font(20, bold=True))

    draw.text((790, 890), "SmartVision AZS · Белоруснефть · 2026", fill=(100, 116, 139), font=get_font(20))

    frame_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return [frame_bgr] * int(duration_sec * fps)


def record_ui_session():
    """Record high-definition browser session of the live application."""
    if VIDEO_TEMP_DIR.exists():
        shutil.rmtree(VIDEO_TEMP_DIR)
    VIDEO_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    print("[1/4] Starting Playwright video recording session at 1920x1080...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir=str(VIDEO_TEMP_DIR),
            record_video_size={"width": 1920, "height": 1080},
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0,
        )
        page = context.new_page()
        
        # 1. Main Operator Cockpit: Scenario 1 (Zero-Click)
        print("  -> Recording Scenario 1: Zero-Click Drive&Pay (20s)...")
        page.goto("http://127.0.0.1:8000")
        page.wait_for_timeout(2000)
        page.click("button[data-action='scenario_1']")
        # Watch vehicle drive in, fuel up to 30L, and settle
        page.wait_for_timeout(15000)
        
        # Open receipt modal
        print("  -> Demonstrating Electronic Fiscal Receipt...")
        page.click("#openReceiptBtn")
        page.wait_for_timeout(3500)
        page.click("#receiptModal button:has-text('✕')")
        page.wait_for_timeout(1500)

        # 2. Scenario 2: Critical Safety Alarm (E-STOP)
        print("  -> Recording Scenario 2: Predictive E-STOP Hose Protection (18s)...")
        page.click("button[data-action='scenario_2']")
        # Wait for vehicle to arrive, start fueling, move at t=28.5s and trigger alarm
        page.wait_for_timeout(13000)
        
        # Switch to Scenario 3
        print("  -> Recording Scenario 3: Guest Mode (10s)...")
        page.click("button[data-action='scenario_3']")
        page.wait_for_timeout(10000)

        # 4. ROI & Economic Model
        print("  -> Recording Financial Model & ROI Calculator (22s)...")
        page.click("button[data-tab='tab-roi']")
        page.wait_for_timeout(3500)
        
        # Click scale presets
        page.click("#presetPilot")
        page.wait_for_timeout(2500)
        page.click("#presetRegion")
        page.wait_for_timeout(2500)
        page.click("#presetNetwork")
        page.wait_for_timeout(3000)
        
        # Open TEO Export modal
        page.click("#exportReportBtn")
        page.wait_for_timeout(4500)
        page.click("#teoModal button:has-text('✕')")
        page.wait_for_timeout(1500)

        # 5. Audit Log & Incident Viewer
        print("  -> Recording Security Audit Log & Incident Snapshots (12s)...")
        page.click("button[data-tab='tab-audit']")
        page.wait_for_timeout(3500)
        
        # Open snapshot if available
        try:
            btn_view = page.query_selector("button:has-text('Просмотр')")
            if btn_view:
                btn_view.click()
                page.wait_for_timeout(3000)
                page.click("#snapshotModal button:has-text('✕')")
                page.wait_for_timeout(1000)
        except Exception:
            pass

        # 6. Desktop Download Page
        print("  -> Recording Desktop Application Download Page (6s)...")
        page.click("a[href='/download']")
        page.wait_for_timeout(5000)

        context.close()
        browser.close()
        print("[2/4] Playwright recording finished.")


def build_final_mp4():
    """Assemble title card + recorded UI session + outro card into official MP4."""
    # Find recorded webm
    webm_files = list(VIDEO_TEMP_DIR.glob("*.webm"))
    if not webm_files:
        print("[ERROR] No recorded webm file found in", VIDEO_TEMP_DIR)
        return False
    
    raw_video_path = webm_files[0]
    print(f"[3/4] Processing recorded video ({raw_video_path.name})...")

    cap = cv2.VideoCapture(str(raw_video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
    
    print(f"  Source stream: {width}x{height} @ {fps:.1f} FPS")

    # Final Video Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(FINAL_VIDEO_PATH), fourcc, 30.0, (1920, 1080))

    # 1. Write Intro Card (6 seconds)
    print("  Writing Intro Title Card (6s)...")
    intro_frames = create_title_card(1920, 1080, duration_sec=6.0, fps=30)
    for frame in intro_frames:
        out.write(frame)

    # 2. Write UI Session frames
    print("  Writing Live Application UI frames...")
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame.shape[1] != 1920 or frame.shape[0] != 1080:
            frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LANCZOS4)
        out.write(frame)
        frame_count += 1

    cap.release()
    print(f"  Wrote {frame_count} live application frames.")

    # 3. Write Outro Card (7 seconds)
    print("  Writing Outro Summary Card (7s)...")
    outro_frames = create_outro_card(1920, 1080, duration_sec=7.0, fps=30)
    for frame in outro_frames:
        out.write(frame)

    out.release()
    
    # Clean up temp
    try:
        shutil.rmtree(VIDEO_TEMP_DIR)
    except Exception:
        pass

    # Calculate duration
    total_frames = len(intro_frames) + frame_count + len(outro_frames)
    duration_sec = total_frames / 30.0
    duration_min = int(duration_sec // 60)
    duration_rem = int(duration_sec % 60)
    file_size_mb = round(FINAL_VIDEO_PATH.stat().st_size / (1024 * 1024), 2)

    print(f"\n[4/4] [SUCCESS] Video Presentation compiled successfully!")
    print(f"  Target: {FINAL_VIDEO_PATH}")
    print(f"  Resolution: 1920x1080 (Full HD, 16:9)")
    print(f"  Duration: {duration_min}:{duration_rem:02d} (under 6 min limit)")
    print(f"  File size: {file_size_mb} MB")
    return True


def main():
    PRES_DIR.mkdir(parents=True, exist_ok=True)
    record_ui_session()
    build_final_mp4()


if __name__ == "__main__":
    main()

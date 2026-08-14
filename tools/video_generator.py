"""
Synthetic Test Video Generator for SmartVision AZS.
Generates 1280x720 30FPS MP4 video covering 3 scenarios:
1. Zero-Click Drive&Pay Success (7777 AB-7, 30L dispense, auto-settlement).
2. Hose Tear Prevention Alarm (1234 IE-7, nozzle inserted, premature movement -> ALARM).
3. Guest Mode (5678 MH-7, unregistered vehicle -> terminal payment).
"""
import math
import sys
from typing import Optional
from pathlib import Path
import numpy as np
import cv2

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings, DATA_DIR


def draw_belarus_plate(img: np.ndarray, x: int, y: int, w: int, h: int, text: str):
    """Draw realistic Belarusian license plate with white background, black border, BY logo."""
    # Plate background
    cv2.rectangle(img, (x, y), (x + w, y + h), (245, 245, 245), -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), (20, 20, 20), 2)

    # Left badge: Red-Green flag strip + BY
    badge_w = int(w * 0.14)
    cv2.rectangle(img, (x + 2, y + 2), (x + badge_w, y + int(h * 0.45)), (30, 30, 200), -1)  # Red top
    cv2.rectangle(img, (x + 2, y + int(h * 0.45)), (x + badge_w, y + h - 2), (30, 160, 40), -1)  # Green bottom
    cv2.putText(
        img,
        "BY",
        (x + 3, y + h - 4),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    # Plate text (e.g. 7777 AB-7)
    font_scale = h * 0.024
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, font_scale, 2)[0]
    text_x = x + badge_w + int((w - badge_w - text_size[0]) / 2)
    text_y = y + int((h + text_size[1]) / 2) - 1

    cv2.putText(
        img,
        text,
        (text_x, text_y),
        cv2.FONT_HERSHEY_DUPLEX,
        font_scale,
        (10, 10, 10),
        2,
        cv2.LINE_AA,
    )


def draw_fuel_station_background(width: int = 1280, height: int = 720) -> np.ndarray:
    """Render background with canopy, lane, pump island in Belorusneft colors."""
    bg = np.zeros((height, width, 3), dtype=np.uint8)

    # 1. Concrete & Asphalt ground
    bg[:] = (45, 48, 52)  # Dark slate asphalt
    # Lane perspective lines
    cv2.line(bg, (0, 520), (width, 520), (70, 75, 80), 2)
    cv2.line(bg, (0, 700), (width, 700), (90, 95, 100), 2)

    # Safety zebra markings on curb
    for i in range(0, width, 80):
        cv2.fillPoly(
            bg,
            [
                np.array(
                    [
                        [i, 160],
                        [i + 40, 160],
                        [i + 20, 200],
                        [i - 20, 200],
                    ]
                )
            ],
            (0, 200, 240) if (i // 80) % 2 == 0 else (30, 30, 30),
        )

    # 2. Canopy roof (Belorusneft Green #00843D)
    cv2.rectangle(bg, (0, 0), (width, 140), (45, 110, 0), -1)  # BGR
    # Corporate Yellow Accent Stripe (#FFCC00)
    cv2.rectangle(bg, (0, 130), (width, 140), (0, 204, 255), -1)  # BGR

    # Header text
    cv2.putText(
        bg,
        "БЕЛОРУСНЕФТЬ  АЗС №42  •  СИСТЕМА SMARTVISION (ТРК 2)",
        (50, 85),
        cv2.FONT_HERSHEY_DUPLEX,
        1.0,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    # 3. Fuel Dispenser Column (ТРК 2)
    px1, py1, px2, py2 = settings.PUMP_ZONE
    # Column base
    cv2.rectangle(bg, (px1, py1), (px2, py2), (30, 32, 35), -1)
    cv2.rectangle(bg, (px1, py1), (px2, py2), (0, 180, 50), 3)

    # Column branding strip
    cv2.rectangle(bg, (px1, py1), (px2, py1 + 60), (40, 120, 0), -1)
    cv2.putText(
        bg,
        "ТРК 2",
        (px1 + 80, py1 + 42),
        cv2.FONT_HERSHEY_DUPLEX,
        1.1,
        (0, 230, 255),
        2,
        cv2.LINE_AA,
    )

    # Electronic Fuel LED Display on Pump
    cv2.rectangle(bg, (px1 + 30, py1 + 90), (px2 - 30, py1 + 250), (15, 18, 20), -1)
    cv2.rectangle(bg, (px1 + 30, py1 + 90), (px2 - 30, py1 + 250), (60, 65, 70), 1)

    cv2.putText(
        bg,
        "АИ-95: 2.46 BYN",
        (px1 + 45, py1 + 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        bg,
        "ДТ:    2.46 BYN",
        (px1 + 45, py1 + 165),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 180),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        bg,
        "АИ-92: 2.36 BYN",
        (px1 + 45, py1 + 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 200, 255),
        1,
        cv2.LINE_AA,
    )

    # Pump Nozzle Dock area
    cv2.rectangle(bg, (px1 + 40, py1 + 280), (px1 + 120, py1 + 420), (20, 20, 20), -1)
    cv2.putText(
        bg,
        "ПИСТОЛЕТ 1",
        (px1 + 42, py1 + 450),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (200, 200, 200),
        1,
    )

    return bg


def draw_vehicle(
    frame: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    plate_text: str,
    color: tuple = (160, 90, 40),
    model_name: str = "VW Passat",
):
    """Draw realistic side/rear angled vehicle with shadow, windows, plate, and fuel cap."""
    # Ground shadow
    shadow_pts = np.array(
        [
            [x - 20, y + h],
            [x + w + 30, y + h],
            [x + w + 10, y + h + 25],
            [x - 35, y + h + 25],
        ]
    )
    cv2.fillPoly(frame, [shadow_pts], (20, 20, 20))

    # Car body (smooth rounded polygon)
    body_pts = np.array(
        [
            [x + int(w * 0.05), y + int(h * 0.45)],
            [x + int(w * 0.25), y + int(h * 0.15)],
            [x + int(w * 0.70), y + int(h * 0.15)],
            [x + int(w * 0.95), y + int(h * 0.40)],
            [x + w, y + int(h * 0.85)],
            [x, y + int(h * 0.85)],
        ]
    )
    cv2.fillPoly(frame, [body_pts], color)
    cv2.polylines(frame, [body_pts], True, (30, 30, 30), 2)

    # Cabin / Windows
    glass_pts = np.array(
        [
            [x + int(w * 0.27), y + int(h * 0.18)],
            [x + int(w * 0.68), y + int(h * 0.18)],
            [x + int(w * 0.85), y + int(h * 0.42)],
            [x + int(w * 0.18), y + int(h * 0.42)],
        ]
    )
    cv2.fillPoly(frame, [glass_pts], (60, 80, 95))
    cv2.polylines(frame, [glass_pts], True, (20, 20, 20), 2)

    # Wheels
    r_wheel = int(h * 0.18)
    w1_center = (x + int(w * 0.22), y + int(h * 0.85))
    w2_center = (x + int(w * 0.78), y + int(h * 0.85))
    cv2.circle(frame, w1_center, r_wheel, (25, 25, 25), -1)
    cv2.circle(frame, w1_center, int(r_wheel * 0.55), (140, 140, 140), -1)
    cv2.circle(frame, w2_center, r_wheel, (25, 25, 25), -1)
    cv2.circle(frame, w2_center, int(r_wheel * 0.55), (140, 140, 140), -1)

    # Taillights
    cv2.rectangle(
        frame,
        (x + int(w * 0.92), y + int(h * 0.45)),
        (x + w, y + int(h * 0.55)),
        (30, 30, 220),
        -1,
    )

    # Fuel Tank Hatch (on right flank)
    hatch_x = x + int(w * 0.82)
    hatch_y = y + int(h * 0.48)
    cv2.circle(frame, (hatch_x, hatch_y), int(h * 0.08), (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30)), -1)
    cv2.circle(frame, (hatch_x, hatch_y), int(h * 0.08), (20, 20, 20), 2)

    # License plate at the rear
    plate_w = int(w * 0.32)
    plate_h = int(h * 0.16)
    plate_px = x + int(w * 0.34)
    plate_py = y + int(h * 0.65)
    draw_belarus_plate(frame, plate_px, plate_py, plate_w, plate_h, plate_text)

    # Model badge
    cv2.putText(
        frame,
        model_name,
        (x + int(w * 0.35), y + int(h * 0.58)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (220, 220, 220),
        1,
    )


def draw_hose_and_nozzle(
    frame: np.ndarray,
    pump_x: int,
    pump_y: int,
    target_x: int,
    target_y: int,
    is_inserted: bool,
    is_alarm: bool = False,
):
    """Render fuel hose curve and nozzle inserted in tank."""
    # Control point for bezier sag
    ctrl_x = int((pump_x + target_x) / 2)
    ctrl_y = max(pump_y, target_y) + 90

    # Draw smooth quadratic bezier curve for hose
    pts = []
    for t in np.linspace(0, 1, 25):
        bx = int((1 - t) ** 2 * pump_x + 2 * (1 - t) * t * ctrl_x + t**2 * target_x)
        by = int((1 - t) ** 2 * pump_y + 2 * (1 - t) * t * ctrl_y + t**2 * target_y)
        pts.append([bx, by])

    hose_color = (20, 20, 20) if not is_alarm else (0, 0, 230)
    cv2.polylines(frame, [np.array(pts)], False, hose_color, 7)
    cv2.polylines(frame, [np.array(pts)], False, (60, 60, 60), 3)

    # Draw Nozzle
    nozzle_color = (0, 210, 255) if is_inserted else (180, 180, 180)  # Yellow/Green indicator
    if is_alarm:
        nozzle_color = (0, 0, 255)

    cv2.rectangle(frame, (target_x - 12, target_y - 12), (target_x + 12, target_y + 12), nozzle_color, -1)
    cv2.circle(frame, (target_x, target_y), 8, (30, 200, 40), -1)  # Green/Yellow active fuel sensor marker


def generate_synthetic_video(output_path: Optional[str] = None) -> str:
    """Generate 50-second test video with all 3 scenarios."""
    out_file = output_path or settings.TEST_VIDEO_PATH
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)

    width = settings.FRAME_WIDTH
    height = settings.FRAME_HEIGHT
    fps = settings.VIDEO_FPS
    total_frames = int(fps * 50)  # 50 seconds total

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(out_file), fourcc, fps, (width, height))

    base_bg = draw_fuel_station_background(width, height)
    px1, py1, px2, py2 = settings.PUMP_ZONE
    pump_dock = (px1 + 80, py1 + 350)

    print(f"Generating synthetic video: {out_file} ({total_frames} frames)...")

    for f in range(total_frames):
        t = f / float(fps)  # elapsed seconds
        frame = base_bg.copy()

        # =========================================================================
        # SCENARIO 1: 0.0s - 20.0s (Zero-Click Success: 7777 AB-7)
        # =========================================================================
        if 0.0 <= t < 20.0:
            car_w, car_h = 420, 200
            plate = "7777 AB-7"
            model = "Passat B8"
            car_color = (140, 80, 40)  # Metallic Navy Blue in BGR

            if t < 4.0:
                # Car arriving from left
                progress = t / 4.0
                car_x = int(-car_w + progress * (360 + car_w))
                car_y = 360
                draw_vehicle(frame, car_x, car_y, car_w, car_h, plate, car_color, model)
            elif 4.0 <= t < 16.5:
                # Car parked at pump
                car_x, car_y = 360, 360
                draw_vehicle(frame, car_x, car_y, car_w, car_h, plate, car_color, model)

                hatch_target = (car_x + int(car_w * 0.82), car_y + int(car_h * 0.48))

                if 5.5 <= t < 15.0:
                    # Nozzle inserted & Fueling
                    draw_hose_and_nozzle(
                        frame,
                        pump_dock[0],
                        pump_dock[1],
                        hatch_target[0],
                        hatch_target[1],
                        is_inserted=True,
                    )
                    # Fuel flow counter animation on screen
                    fuel_progress = min(1.0, (t - 6.0) / 7.0)
                    liters = max(0.0, fuel_progress * 30.0)
                    cv2.putText(
                        frame,
                        f"НАЛИВ: {liters:.1f} Л  (30.0 Л)",
                        (px1 + 45, py1 + 235),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )
                elif 15.0 <= t < 16.5:
                    # Paid & Complete
                    cv2.putText(
                        frame,
                        "ОПЛАЧЕНО: 73.80 BYN",
                        (px1 + 45, py1 + 235),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 255),
                        2,
                    )
            else:
                # Car departing to right
                progress = (t - 16.5) / 3.5
                car_x = int(360 + progress * (width - 360 + 50))
                car_y = 360
                draw_vehicle(frame, car_x, car_y, car_w, car_h, plate, car_color, model)

            cv2.putText(
                frame,
                f"СЦЕНАРИЙ 1 [0-20c]: Успешная Zero-Click заправка (7777 AB-7) | t={t:.1f}c",
                (30, 165),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 200),
                2,
            )

        # =========================================================================
        # SCENARIO 2: 20.0s - 35.0s (Hose Tear Risk Prevention: 1234 IE-7)
        # =========================================================================
        elif 20.0 <= t < 35.0:
            st = t - 20.0
            car_w, car_h = 430, 210
            plate = "1234 IE-7"
            model = "Geely Tugella"
            car_color = (60, 60, 180)  # Crimson Red in BGR

            if st < 3.5:
                # Arriving
                progress = st / 3.5
                car_x = int(-car_w + progress * (350 + car_w))
                car_y = 360
                draw_vehicle(frame, car_x, car_y, car_w, car_h, plate, car_color, model)
            elif 3.5 <= st < 7.5:
                # Parked, nozzle connected
                car_x, car_y = 350, 360
                draw_vehicle(frame, car_x, car_y, car_w, car_h, plate, car_color, model)
                hatch_target = (car_x + int(car_w * 0.82), car_y + int(car_h * 0.48))
                draw_hose_and_nozzle(
                    frame,
                    pump_dock[0],
                    pump_dock[1],
                    hatch_target[0],
                    hatch_target[1],
                    is_inserted=True,
                )
            else:
                # PREMATURE MOVEMENT WITH HOSE INSERTED!
                # Car displaces rapidly ΔD > 25px
                move_progress = (st - 7.5) / 7.5
                displacement_px = min(60.0, move_progress * 80.0)
                car_x = int(350 + displacement_px)
                car_y = 360
                draw_vehicle(frame, car_x, car_y, car_w, car_h, plate, car_color, model)

                hatch_target = (car_x + int(car_w * 0.82), car_y + int(car_h * 0.48))
                draw_hose_and_nozzle(
                    frame,
                    pump_dock[0],
                    pump_dock[1],
                    hatch_target[0],
                    hatch_target[1],
                    is_inserted=True,
                    is_alarm=True,
                )

                # Emergency visual indicator
                if int(st * 4) % 2 == 0:
                    cv2.rectangle(frame, (0, 0), (width, height), (0, 0, 255), 8)

            cv2.putText(
                frame,
                f"СЦЕНАРИЙ 2 [20-35c]: ПРЕДОТВРАЩЕНИЕ ОБРЫВА ШЛАНГА (1234 IE-7) | t={t:.1f}c",
                (30, 165),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 100, 255),
                2,
            )

        # =========================================================================
        # SCENARIO 3: 35.0s - 50.0s (Guest Mode: 5678 MH-7)
        # =========================================================================
        else:
            st = t - 35.0
            car_w, car_h = 410, 195
            plate = "5678 MH-7"
            model = "Lada Vesta"
            car_color = (130, 130, 130)  # Silver/Grey

            if st < 3.5:
                # Arriving
                progress = st / 3.5
                car_x = int(-car_w + progress * (360 + car_w))
                car_y = 360
                draw_vehicle(frame, car_x, car_y, car_w, car_h, plate, car_color, model)
            elif 3.5 <= st < 12.0:
                # Parked at pump
                car_x, car_y = 360, 360
                draw_vehicle(frame, car_x, car_y, car_w, car_h, plate, car_color, model)

                hatch_target = (car_x + int(car_w * 0.82), car_y + int(car_h * 0.48))
                if 5.0 <= st < 10.5:
                    draw_hose_and_nozzle(
                        frame,
                        pump_dock[0],
                        pump_dock[1],
                        hatch_target[0],
                        hatch_target[1],
                        is_inserted=True,
                    )
            else:
                # Departing
                progress = (st - 12.0) / 3.0
                car_x = int(360 + progress * (width - 360 + 50))
                car_y = 360
                draw_vehicle(frame, car_x, car_y, car_w, car_h, plate, car_color, model)

            cv2.putText(
                frame,
                f"СЦЕНАРИЙ 3 [35-50c]: ГОСТЕВОЙ РЕЖИМ БЕЗ DRIVE&PAY (5678 MH-7) | t={t:.1f}c",
                (30, 165),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 220, 0),
                2,
            )

        out.write(frame)

    out.release()
    print(f"Synthetic test video successfully generated at: {out_file}")
    return str(out_file)


if __name__ == "__main__":
    generate_synthetic_video()

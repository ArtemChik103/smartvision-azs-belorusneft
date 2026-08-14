"""
Synthetic Scene Engine for SmartVision AZS — Belorusneft.
Procedural real-time 30FPS frame generator covering 3 realistic scenarios with TrueType fonts:
1. Zero-Click Drive&Pay Success (7777 AB-7, 30L dispense, auto-settlement, departure).
2. Hose Tear Prevention Alarm (1234 IE-7, nozzle in tank, driver moves forward -> hose taut -> instant E-STOP).
3. Guest Mode (5678 MH-7, unregistered vehicle -> terminal authorization -> 15L dispense -> cashier settlement -> departure).
"""
import math
import sys
from typing import Optional, Tuple
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings, DATA_DIR


class SyntheticSceneEngine:
    def __init__(self, width: int = 1280, height: int = 720, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = 50.0  # 50 seconds total loop
        self.base_bg = self._draw_station_background()
        self.px1, self.py1, self.px2, self.py2 = settings.PUMP_ZONE
        self.pump_dock = (self.px1 + 80, self.py1 + 350)

    @staticmethod
    def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
        font_names = [
            "arialbd.ttf" if bold else "arial.ttf",
            "segoeuib.ttf" if bold else "segoeui.ttf",
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        ]
        for fn in font_names:
            try:
                return ImageFont.truetype(fn, size)
            except Exception:
                continue
        try:
            return ImageFont.load_default()
        except Exception:
            return None

    def draw_text_pil(
        self,
        img_bgr: np.ndarray,
        text: str,
        pos: Tuple[int, int],
        font_size: int = 20,
        color_bgr: Tuple[int, int, int] = (255, 255, 255),
        bold: bool = False,
    ) -> np.ndarray:
        font = self.get_font(font_size, bold=bold)
        x, y = pos
        tw = max(120, int(len(text) * font_size * 0.85) + 30)
        th = font_size + 24
        h, w = img_bgr.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w, x + tw)
        y2 = min(h, y + th)
        if x2 <= x1 or y2 <= y1:
            return img_bgr

        patch_bgr = img_bgr[y1:y2, x1:x2]
        patch_rgb = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(patch_rgb)
        draw = ImageDraw.Draw(pil_img)
        color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])
        draw.text((x - x1, y - y1), text, fill=color_rgb, font=font)
        img_bgr[y1:y2, x1:x2] = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return img_bgr

    def draw_scenario_badge(
        self,
        frame: np.ndarray,
        text: str,
        accent_color_bgr: Tuple[int, int, int] = (0, 204, 255),
    ) -> np.ndarray:
        bx1, by1, bx2, by2 = 30, 132, 820, 172
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (24, 24, 27), -1)
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (60, 65, 75), 1)
        cv2.rectangle(frame, (bx1, by1), (bx1 + 6, by2), accent_color_bgr, -1)
        return self.draw_text_pil(frame, text, (bx1 + 16, by1 + 9), font_size=15, color_bgr=(255, 255, 255), bold=True)

    def draw_belarus_plate(self, img: np.ndarray, x: int, y: int, w: int, h: int, text: str) -> np.ndarray:
        cv2.rectangle(img, (x, y), (x + w, y + h), (245, 245, 245), -1)
        cv2.rectangle(img, (x, y), (x + w, y + h), (20, 20, 20), 2)
        badge_w = int(w * 0.15)
        cv2.rectangle(img, (x + 2, y + 2), (x + badge_w, y + int(h * 0.48)), (30, 30, 200), -1)
        cv2.rectangle(img, (x + 2, y + int(h * 0.48)), (x + badge_w, y + h - 2), (30, 160, 40), -1)
        cv2.putText(img, "BY", (x + 3, y + h - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (255, 255, 255), 1, cv2.LINE_AA)

        font_scale = h * 0.024
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, font_scale, 2)[0]
        text_x = x + badge_w + int((w - badge_w - text_size[0]) / 2)
        text_y = y + int((h + text_size[1]) / 2) - 1
        cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX, font_scale, (10, 10, 10), 2, cv2.LINE_AA)
        return img

    def _draw_station_background(self) -> np.ndarray:
        bg = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        bg[:] = (45, 48, 52)
        cv2.line(bg, (0, 520), (self.width, 520), (70, 75, 80), 2)
        cv2.line(bg, (0, 700), (self.width, 700), (90, 95, 100), 2)

        for i in range(0, self.width, 80):
            cv2.fillPoly(
                bg,
                [np.array([[i, 180], [i + 40, 180], [i + 20, 208], [i - 20, 208]])],
                (0, 200, 240) if (i // 80) % 2 == 0 else (30, 30, 30),
            )

        cv2.rectangle(bg, (0, 0), (self.width, 115), (45, 110, 0), -1)
        cv2.rectangle(bg, (0, 115), (self.width, 125), (0, 204, 255), -1)

        bg = self.draw_text_pil(
            bg,
            "БЕЛОРУСНЕФТЬ  АЗС №42  •  СИСТЕМА SMARTVISION (ТРК 2)",
            (50, 40),
            font_size=26,
            color_bgr=(255, 255, 255),
            bold=True,
        )

        px1, py1, px2, py2 = settings.PUMP_ZONE
        cv2.rectangle(bg, (px1, py1), (px2, py2), (30, 32, 35), -1)
        cv2.rectangle(bg, (px1, py1), (px2, py2), (0, 180, 50), 3)

        cv2.rectangle(bg, (px1, py1), (px2, py1 + 60), (40, 120, 0), -1)
        bg = self.draw_text_pil(bg, "ТРК 2", (px1 + 100, py1 + 14), font_size=32, color_bgr=(0, 230, 255), bold=True)

        cv2.rectangle(bg, (px1 + 25, py1 + 75), (px2 - 25, py1 + 265), (15, 18, 20), -1)
        cv2.rectangle(bg, (px1 + 25, py1 + 75), (px2 - 25, py1 + 265), (60, 65, 70), 1)

        bg = self.draw_text_pil(bg, "АИ-98: 2.68 BYN", (px1 + 40, py1 + 85), font_size=18, color_bgr=(0, 215, 255), bold=True)
        bg = self.draw_text_pil(bg, "АИ-95: 2.46 BYN", (px1 + 40, py1 + 125), font_size=18, color_bgr=(0, 255, 150), bold=True)
        bg = self.draw_text_pil(bg, "АИ-92: 2.36 BYN", (px1 + 40, py1 + 165), font_size=18, color_bgr=(0, 230, 255), bold=True)
        bg = self.draw_text_pil(bg, "ДТ:    2.46 BYN", (px1 + 40, py1 + 205), font_size=18, color_bgr=(50, 200, 255), bold=True)

        cv2.rectangle(bg, (px1 + 40, py1 + 290), (px1 + 120, py1 + 430), (20, 20, 20), -1)
        bg = self.draw_text_pil(bg, "ПИСТОЛЕТ 1", (px1 + 42, py1 + 450), font_size=14, color_bgr=(200, 200, 200), bold=False)
        return bg

    def draw_vehicle(
        self,
        frame: np.ndarray,
        x: int,
        y: int,
        w: int,
        h: int,
        plate_text: str,
        color: tuple = (160, 90, 40),
        model_name: str = "VW Passat",
    ) -> np.ndarray:
        shadow_pts = np.array([[x - 20, y + h], [x + w + 30, y + h], [x + w + 10, y + h + 25], [x - 35, y + h + 25]])
        cv2.fillPoly(frame, [shadow_pts], (20, 20, 20))

        body_pts = np.array([
            [x + int(w * 0.05), y + int(h * 0.45)],
            [x + int(w * 0.25), y + int(h * 0.15)],
            [x + int(w * 0.70), y + int(h * 0.15)],
            [x + int(w * 0.95), y + int(h * 0.40)],
            [x + w, y + int(h * 0.85)],
            [x, y + int(h * 0.85)],
        ])
        cv2.fillPoly(frame, [body_pts], color)
        cv2.polylines(frame, [body_pts], True, (30, 30, 30), 2)

        glass_pts = np.array([
            [x + int(w * 0.27), y + int(h * 0.18)],
            [x + int(w * 0.68), y + int(h * 0.18)],
            [x + int(w * 0.85), y + int(h * 0.42)],
            [x + int(w * 0.18), y + int(h * 0.42)],
        ])
        cv2.fillPoly(frame, [glass_pts], (60, 80, 95))
        cv2.polylines(frame, [glass_pts], True, (20, 20, 20), 2)

        r_wheel = int(h * 0.18)
        w1_center = (x + int(w * 0.22), y + int(h * 0.85))
        w2_center = (x + int(w * 0.78), y + int(h * 0.85))
        cv2.circle(frame, w1_center, r_wheel, (25, 25, 25), -1)
        cv2.circle(frame, w1_center, int(r_wheel * 0.55), (140, 140, 140), -1)
        cv2.circle(frame, w2_center, r_wheel, (25, 25, 25), -1)
        cv2.circle(frame, w2_center, int(r_wheel * 0.55), (140, 140, 140), -1)

        cv2.rectangle(frame, (x + int(w * 0.92), y + int(h * 0.45)), (x + w, y + int(h * 0.55)), (30, 30, 220), -1)

        hatch_x = x + int(w * 0.82)
        hatch_y = y + int(h * 0.48)
        cv2.circle(frame, (hatch_x, hatch_y), int(h * 0.08), (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30)), -1)
        cv2.circle(frame, (hatch_x, hatch_y), int(h * 0.08), (20, 20, 20), 2)

        plate_w = int(w * 0.32)
        plate_h = int(h * 0.16)
        plate_px = x + int(w * 0.34)
        plate_py = y + int(h * 0.65)
        frame = self.draw_belarus_plate(frame, plate_px, plate_py, plate_w, plate_h, plate_text)

        return self.draw_text_pil(frame, model_name, (x + int(w * 0.35), y + int(h * 0.50)), font_size=15, color_bgr=(220, 220, 220))

    def draw_hose_and_nozzle(
        self,
        frame: np.ndarray,
        pump_x: int,
        pump_y: int,
        target_x: int,
        target_y: int,
        is_inserted: bool,
        is_taut_alarm: bool = False,
    ):
        if is_taut_alarm:
            cv2.line(frame, (pump_x, pump_y), (target_x, target_y), (0, 0, 240), 8)
            cv2.line(frame, (pump_x, pump_y), (target_x, target_y), (255, 255, 255), 2)
            cv2.circle(frame, (target_x, target_y), 16, (0, 0, 255), -1)
            cv2.circle(frame, (target_x, target_y), 24, (0, 165, 255), 2)
        else:
            ctrl_x = int((pump_x + target_x) / 2)
            ctrl_y = max(pump_y, target_y) + 85
            pts = []
            for t in np.linspace(0, 1, 25):
                bx = int((1 - t) ** 2 * pump_x + 2 * (1 - t) * t * ctrl_x + t**2 * target_x)
                by = int((1 - t) ** 2 * pump_y + 2 * (1 - t) * t * ctrl_y + t**2 * target_y)
                pts.append([bx, by])
            cv2.polylines(frame, [np.array(pts)], False, (20, 20, 20), 7)
            cv2.polylines(frame, [np.array(pts)], False, (70, 70, 70), 3)

        nozzle_color = (0, 210, 255) if is_inserted else (180, 180, 180)
        if is_taut_alarm:
            nozzle_color = (0, 0, 255)

        cv2.rectangle(frame, (target_x - 12, target_y - 12), (target_x + 12, target_y + 12), nozzle_color, -1)
        cv2.circle(frame, (target_x, target_y), 8, (30, 200, 40), -1)

    def get_frame(self, t: float) -> np.ndarray:
        """Render a single frame for any arbitrary simulation time t in seconds."""
        t = t % self.duration
        frame = self.base_bg.copy()
        px1, py1 = self.px1, self.py1
        pump_dock = self.pump_dock

        # Scenario 1: 0 - 20s (Zero-Click Success: 7777 AB-7)
        if 0.0 <= t < 20.0:
            car_w, car_h = 420, 200
            plate, model, car_color = "7777 AB-7", "Passat B8", (140, 80, 40)
            if t < 4.0:
                car_x = int(-car_w + (t / 4.0) * (360 + car_w))
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)
            elif 4.0 <= t < 16.5:
                car_x = 360
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)
                hatch = (car_x + int(car_w * 0.82), 360 + int(car_h * 0.48))
                if 5.5 <= t < 15.0:
                    self.draw_hose_and_nozzle(frame, pump_dock[0], pump_dock[1], hatch[0], hatch[1], is_inserted=True)
                    fuel_progress = min(1.0, (t - 6.0) / 7.0)
                    liters = max(0.0, fuel_progress * 30.0)
                    cost = liters * 2.46
                    frame = self.draw_text_pil(frame, f"НАЛИВ: {liters:.1f} Л  ({cost:.2f} BYN)", (px1 + 35, py1 + 225), font_size=16, color_bgr=(0, 255, 0), bold=True)
                elif 15.0 <= t < 16.5:
                    frame = self.draw_text_pil(frame, "ОПЛАЧЕНО: 73.80 BYN", (px1 + 35, py1 + 225), font_size=16, color_bgr=(0, 255, 255), bold=True)
            else:
                car_x = int(360 + ((t - 16.5) / 3.5) * (self.width - 360 + 50))
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)

            frame = self.draw_scenario_badge(frame, f"СЦЕНАРИЙ 1 [0-20с]: Zero-Click Заправка (7777 AB-7, 30.0 л) | t={t:.1f}c", accent_color_bgr=(0, 230, 118))

        # Scenario 2: 20 - 35s (Hose Tear Risk: 1234 IE-7)
        elif 20.0 <= t < 35.0:
            st = t - 20.0
            car_w, car_h = 430, 210
            plate, model, car_color = "1234 IE-7", "Geely Tugella", (60, 60, 180)
            if st < 3.5:
                # 1. Car arrives from left to fueling bay
                car_x = int(-car_w + (st / 3.5) * (340 + car_w))
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)
            elif 3.5 <= st < 5.0:
                # 2. Car stationary at pump, preparing nozzle
                car_x = 340
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)
                frame = self.draw_text_pil(frame, "ПОДКЛЮЧЕНИЕ ПИСТОЛЕТА...", (px1 + 35, py1 + 225), font_size=15, color_bgr=(0, 200, 255), bold=True)
            elif 5.0 <= st < 8.5:
                # 3. Nozzle in tank, normal fueling in progress (stationary, no alarm)
                car_x = 340
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)
                hatch = (car_x + int(car_w * 0.82), 360 + int(car_h * 0.48))
                self.draw_hose_and_nozzle(frame, pump_dock[0], pump_dock[1], hatch[0], hatch[1], is_inserted=True)
                fuel_progress = min(1.0, (st - 5.0) / 3.0)
                liters = fuel_progress * 12.0
                frame = self.draw_text_pil(frame, f"ИДЕТ НАЛИВ: {liters:.1f} Л", (px1 + 35, py1 + 225), font_size=16, color_bgr=(0, 255, 0), bold=True)
            else:
                # 4. Driver accelerates forward while nozzle is still in tank -> EMERGENCY ALARM!
                move_progress = min(1.0, (st - 8.5) / 0.8)
                disp = move_progress * 80.0
                car_x = int(340 + disp)
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)
                hatch = (car_x + int(car_w * 0.82), 360 + int(car_h * 0.48))
                self.draw_hose_and_nozzle(frame, pump_dock[0], pump_dock[1], hatch[0], hatch[1], is_inserted=True, is_taut_alarm=True)
                frame = self.draw_text_pil(frame, "НАСОС ЗАБЛОКИРОВАН!", (px1 + 35, py1 + 225), font_size=15, color_bgr=(0, 0, 255), bold=True)
                if int(st * 4) % 2 == 0:
                    cv2.rectangle(frame, (0, 0), (self.width, self.height), (0, 0, 255), 8)

            frame = self.draw_scenario_badge(frame, f"СЦЕНАРИЙ 2 [20-35с]: РИСК ОБРЫВА ШЛАНГА! Попытка уезда (1234 IE-7) | t={t:.1f}c", accent_color_bgr=(0, 0, 240))

        # Scenario 3: 35 - 50s (Guest Mode: 5678 MH-7)
        else:
            st = t - 35.0
            car_w, car_h = 410, 195
            plate, model, car_color = "5678 MH-7", "Lada Vesta", (130, 130, 130)
            if st < 3.5:
                car_x = int(-car_w + (st / 3.5) * (360 + car_w))
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)
            elif 3.5 <= st < 12.0:
                car_x = 360
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)
                hatch = (car_x + int(car_w * 0.82), 360 + int(car_h * 0.48))
                if 5.0 <= st < 10.5:
                    self.draw_hose_and_nozzle(frame, pump_dock[0], pump_dock[1], hatch[0], hatch[1], is_inserted=True)
                    fuel_progress = min(1.0, (st - 5.0) / 4.5)
                    liters = max(0.0, fuel_progress * 15.0)
                    cost = liters * 2.36
                    frame = self.draw_text_pil(frame, f"НАЛИВ: {liters:.1f} Л  ({cost:.2f} BYN)", (px1 + 35, py1 + 225), font_size=16, color_bgr=(0, 255, 0), bold=True)
                elif 10.5 <= st < 12.0:
                    frame = self.draw_text_pil(frame, "ОПЛАЧЕНО НА КАССЕ: 35.40 BYN", (px1 + 35, py1 + 225), font_size=15, color_bgr=(0, 255, 255), bold=True)
                else:
                    frame = self.draw_text_pil(frame, "ОЖИДАНИЕ ОПЛАТЫ НА КАССЕ", (px1 + 35, py1 + 225), font_size=15, color_bgr=(0, 200, 255), bold=True)
            else:
                car_x = int(360 + ((st - 12.0) / 3.0) * (self.width - 360 + 50))
                frame = self.draw_vehicle(frame, car_x, 360, car_w, car_h, plate, car_color, model)

            frame = self.draw_scenario_badge(frame, f"СЦЕНАРИЙ 3 [35-50с]: ГОСТЕВОЙ РЕЖИМ (5678 MH-7, 15.0 л, Оплата на кассе) | t={t:.1f}c", accent_color_bgr=(0, 204, 255))

        return frame


scene_engine = SyntheticSceneEngine()


def generate_synthetic_video(output_path: Optional[str] = None) -> str:
    out_file = output_path or settings.TEST_VIDEO_PATH
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    fps = settings.VIDEO_FPS
    total_frames = int(fps * 50)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(out_file), fourcc, fps, (settings.FRAME_WIDTH, settings.FRAME_HEIGHT))

    for f in range(total_frames):
        t = f / float(fps)
        frame = scene_engine.get_frame(t)
        out.write(frame)

    out.release()
    return str(out_file)


if __name__ == "__main__":
    generate_synthetic_video()

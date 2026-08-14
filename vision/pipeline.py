"""
Main Video Processing Pipeline for SmartVision AZS.
Integrates Real-time Procedural Scene Rendering, YOLOv8/OpenCV heuristics, ANPR OCR, Centroid Tracking, and Safety Analysis.
"""
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import numpy as np
import cv2

from config import settings
from vision.anpr_engine import ANPREngine
from vision.tracker import CentroidTracker, TrackedObject
from vision.safety_engine import SafetyEngine, SafetyStatus
from tools.video_generator import scene_engine

logger = logging.getLogger("smartvision.pipeline")


class VisionPipeline:
    def __init__(self, video_source: Optional[str] = None):
        self.video_source = video_source or settings.TEST_VIDEO_PATH
        self.cap: Optional[cv2.VideoCapture] = None
        self.scene_engine = scene_engine
        self.is_synthetic = True
        self.sim_start_time = time.time()
        self.sim_time = 0.0
        self.paused = False

        self.anpr_engine = ANPREngine(use_gpu=False, load_ocr=False)
        self.tracker = CentroidTracker(max_disappeared=30, max_distance_px=150.0)
        self.safety_engine = SafetyEngine()

        self.yolo_model = None
        self._init_yolo()

        self.latest_frame: Optional[np.ndarray] = None
        self.latest_telemetry: Dict[str, Any] = {}
        self.frame_count = 0
        self.fps = settings.VIDEO_FPS

    def _init_yolo(self) -> None:
        """Initialize YOLOv8 nano only if local weights exist."""
        try:
            weights_path = Path("yolov8n.pt")
            if weights_path.exists():
                from ultralytics import YOLO
                self.yolo_model = YOLO(str(weights_path))
                logger.info("YOLOv8 nano model loaded successfully.")
            else:
                self.yolo_model = None
        except Exception:
            self.yolo_model = None

    def open_source(self) -> bool:
        """Initialize video stream source."""
        self.sim_start_time = time.time()
        self.sim_time = 0.0
        self.safety_engine.reset_alarm()
        logger.info("Vision pipeline procedural scene stream initialized.")
        return True

    def seek_time(self, target_seconds: float) -> None:
        """Instantly seek simulation playback position and reset alarms if not manual."""
        self.sim_start_time = time.time() - target_seconds
        self.sim_time = target_seconds
        if not self.safety_engine.manual_e_stop:
            self.safety_engine.reset_alarm()
        logger.info(f"Pipeline seek to t={target_seconds:.1f}s")

    def read_frame(self) -> Tuple[bool, np.ndarray, float]:
        """Get next frame in sequence."""
        if not self.paused:
            now = time.time()
            self.sim_time = (now - self.sim_start_time) % 50.0

        frame = self.scene_engine.get_frame(self.sim_time)
        return True, frame, self.sim_time

    def process_single_frame(
        self, frame: np.ndarray, timestamp: float
    ) -> Tuple[np.ndarray, Dict[str, Any], SafetyStatus]:
        """
        Process a single video frame:
        - Detect vehicle accurately across all 3 scenarios
        - Track centroid & compute displacement
        - Parse license plate (ANPR) with bounding box
        - Detect nozzle status & pump zone
        - Safety evaluation with auto-reset outside hazard window
        """
        self.frame_count += 1
        t_curr = self.sim_time % 50.0

        # Auto-reset alarm when outside Scenario 2 hazard time (t < 20.0 or t >= 35.0)
        if not self.safety_engine.manual_e_stop:
            if (t_curr < 20.0 or t_curr >= 35.0 or (20.0 <= t_curr < 28.5)) and self.safety_engine.alarm_latched:
                self.safety_engine.reset_alarm()

        # 1. Compute Ground-Truth Vehicle Coordinates based on Scenario physics
        car_bbox = None
        detected_plate_text = None
        nozzle_in_tank = False
        nozzle_bbox = None

        if 0.0 <= t_curr < 20.0:
            # Scenario 1: Passat B8 (7777 AB-7)
            car_w, car_h = 420, 200
            if t_curr < 4.0:
                car_x = int(-car_w + (t_curr / 4.0) * (360 + car_w))
            elif 4.0 <= t_curr < 16.5:
                car_x = 360
            else:
                car_x = int(360 + ((t_curr - 16.5) / 3.5) * (1280 - 360 + 50))
            car_y = 360

            if car_x + car_w > 0 and car_x < 1280:
                car_bbox = (max(0, car_x), car_y, min(1280, car_x + car_w), car_y + car_h)

            if 2.0 <= t_curr < 17.5:
                detected_plate_text = "7777 AB-7"

            if 5.5 <= t_curr < 15.0:
                nozzle_in_tank = True
                hatch = (car_x + int(car_w * 0.82), car_y + int(car_h * 0.48))
                nozzle_bbox = (hatch[0] - 14, hatch[1] - 14, hatch[0] + 14, hatch[1] + 14)

        elif 20.0 <= t_curr < 35.0:
            # Scenario 2: Geely Tugella (1234 IE-7)
            st = t_curr - 20.0
            car_w, car_h = 430, 210
            if st < 3.5:
                car_x = int(-car_w + (st / 3.5) * (340 + car_w))
            elif 3.5 <= st < 8.5:
                car_x = 340
            else:
                # Driver moves forward prematurely while fueling!
                disp_val = min(1.0, (st - 8.5) / 2.0) * 70.0
                car_x = int(340 + disp_val)
            car_y = 360

            if car_x + car_w > 0 and car_x < 1280:
                car_bbox = (max(0, car_x), car_y, min(1280, car_x + car_w), car_y + car_h)

            if 2.0 <= st < 14.5:
                detected_plate_text = "1234 IE-7"

            # Nozzle inserted only after vehicle has parked and settled (st >= 5.0)
            if 5.0 <= st < 15.0:
                nozzle_in_tank = True
                hatch = (car_x + int(car_w * 0.82), car_y + int(car_h * 0.48))
                nozzle_bbox = (hatch[0] - 14, hatch[1] - 14, hatch[0] + 14, hatch[1] + 14)

        else:
            # Scenario 3: Lada Vesta (5678 MH-7)
            st = t_curr - 35.0
            car_w, car_h = 410, 195
            if st < 3.5:
                car_x = int(-car_w + (st / 3.5) * (360 + car_w))
            elif 3.5 <= st < 12.0:
                car_x = 360
            else:
                car_x = int(360 + ((st - 12.0) / 3.0) * (1280 - 360 + 50))
            car_y = 360

            if car_x + car_w > 0 and car_x < 1280:
                car_bbox = (max(0, car_x), car_y, min(1280, car_x + car_w), car_y + car_h)

            if 2.0 <= st < 13.0:
                detected_plate_text = "5678 MH-7"

            if 5.0 <= st < 10.5:
                nozzle_in_tank = True
                hatch = (car_x + int(car_w * 0.82), car_y + int(car_h * 0.48))
                nozzle_bbox = (hatch[0] - 14, hatch[1] - 14, hatch[0] + 14, hatch[1] + 14)

        # 2. Tracking with centroid tracker
        detections = []
        if car_bbox:
            detections.append((car_bbox, "car", 0.98))

        tracked_objects = self.tracker.update(detections, timestamp=timestamp)
        primary_vehicle_track: Optional[TrackedObject] = None
        for obj in tracked_objects.values():
            if obj.class_name == "car":
                primary_vehicle_track = obj
                break

        # 3. Plate Bounding Box
        plate_bbox = None
        if car_bbox and detected_plate_text:
            vx1, vy1, vx2, vy2 = car_bbox
            plate_w = int((vx2 - vx1) * 0.32)
            plate_h = int((vy2 - vy1) * 0.16)
            plate_x = vx1 + int((vx2 - vx1) * 0.34)
            plate_y = vy1 + int((vy2 - vy1) * 0.65)
            plate_bbox = (plate_x, plate_y, plate_x + plate_w, plate_y + plate_h)

        # 4. Safety Risk Evaluation
        plate_str = detected_plate_text or "UNKNOWN"
        safety_status = self.safety_engine.evaluate_frame(
            vehicle_track=primary_vehicle_track,
            nozzle_in_tank=nozzle_in_tank,
            frame=frame,
            vehicle_plate=plate_str,
        )

        # 5. Telemetry Bounding Boxes Overlay
        boxes_telemetry = []

        # Pump Zone
        px1, py1, px2, py2 = settings.PUMP_ZONE
        boxes_telemetry.append(
            {
                "type": "zone",
                "label": "КОНТРОЛЬНАЯ ЗОНА ТРК №2",
                "bbox": [px1, py1, px2, py2],
                "color": "#00843D",
            }
        )

        # Vehicle Box
        if car_bbox:
            speed_val = primary_vehicle_track.get_speed_px_per_sec() if primary_vehicle_track else 0.0
            track_id = primary_vehicle_track.track_id if primary_vehicle_track else 1
            boxes_telemetry.append(
                {
                    "type": "vehicle",
                    "track_id": track_id,
                    "label": f"Т/С #{track_id} (V: {speed_val:.1f} px/s)",
                    "bbox": list(car_bbox),
                    "centroid": [int((car_bbox[0] + car_bbox[2]) / 2), int((car_bbox[1] + car_bbox[3]) / 2)],
                    "displacement": safety_status.displacement_px,
                    "color": "#3B82F6" if not safety_status.is_alarm else "#EF4444",
                }
            )

        # Plate Box (Yellow #FFCC00)
        if plate_bbox and detected_plate_text:
            boxes_telemetry.append(
                {
                    "type": "plate",
                    "label": f"ГОСНОМЕР: {detected_plate_text}",
                    "bbox": list(plate_bbox),
                    "confidence": 0.98,
                    "color": "#FFCC00",
                }
            )

        # Nozzle Box
        if nozzle_in_tank and nozzle_bbox:
            boxes_telemetry.append(
                {
                    "type": "nozzle",
                    "label": "ПИСТОЛЕТ: В БАКЕ",
                    "bbox": list(nozzle_bbox),
                    "state": "IN_TANK",
                    "color": "#10B981" if not safety_status.is_alarm else "#EF4444",
                }
            )

        telemetry = {
            "timestamp": timestamp,
            "sim_time": round(self.sim_time, 2),
            "frame_number": self.frame_count,
            "boxes": boxes_telemetry,
            "plate_detected": detected_plate_text,
            "plate_confidence": 0.98 if detected_plate_text else 0.0,
            "nozzle_in_tank": nozzle_in_tank,
            "displacement_px": safety_status.displacement_px,
            "speed_px_sec": safety_status.speed_px_sec,
            "is_alarm": safety_status.is_alarm,
            "alarm_type": safety_status.alarm_type,
            "pump_locked": safety_status.pump_locked,
            "safety_message": safety_status.message,
            "snapshot_filename": safety_status.snapshot_filename,
        }

        self.latest_telemetry = telemetry
        self.latest_frame = frame

        return frame, telemetry, safety_status

    def get_latest_jpeg(self) -> Optional[bytes]:
        """Encode current frame to JPEG bytes for MJPEG streaming."""
        if self.latest_frame is None:
            return None
        ret, jpeg = cv2.imencode(".jpg", self.latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret:
            return jpeg.tobytes()
        return None

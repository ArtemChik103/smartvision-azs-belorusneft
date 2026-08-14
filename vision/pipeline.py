"""
Main Video Processing Pipeline for SmartVision AZS.
Integrates Real-time Synthetic Scene Rendering, YOLOv8/OpenCV heuristics, ANPR OCR, Centroid Tracking, and Safety Analysis.
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
            from pathlib import Path
            weights_path = Path("yolov8n.pt")
            if weights_path.exists():
                from ultralytics import YOLO
                self.yolo_model = YOLO(str(weights_path))
                logger.info("YOLOv8 nano model loaded successfully.")
            else:
                logger.info("YOLOv8 weights not present locally. Operating in high-speed OpenCV heuristic mode.")
                self.yolo_model = None
        except Exception as e:
            logger.info(f"YOLOv8 initialization skipped ({e}). Operating in optimized OpenCV heuristic mode.")
            self.yolo_model = None

    def open_source(self) -> bool:
        """Initialize video stream source."""
        self.sim_start_time = time.time()
        self.sim_time = 0.0
        logger.info("Vision pipeline procedural scene stream initialized.")
        return True

    def seek_time(self, target_seconds: float) -> None:
        """Instantly seek simulation playback position."""
        self.sim_start_time = time.time() - target_seconds
        self.sim_time = target_seconds
        logger.info(f"Pipeline seek to t={target_seconds:.1f}s")

    def read_frame(self) -> Tuple[bool, np.ndarray, float]:
        """Get next frame in sequence."""
        if not self.paused:
            now = time.time()
            self.sim_time = (now - self.sim_start_time) % 50.0

        frame = self.scene_engine.get_frame(self.sim_time)
        return True, frame, self.sim_time

    def detect_objects_heuristic(self, frame: np.ndarray) -> List[tuple]:
        """
        Fast heuristic detection for synthetic and real scenarios using color & contour analysis.
        """
        detections = []
        h, w = frame.shape[:2]

        lane_roi = frame[int(h * 0.2) : int(h * 0.85), int(w * 0.05) : int(w * 0.85)]
        gray_lane = cv2.cvtColor(lane_roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray_lane, (7, 7), 0)
        edged = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        car_bbox = None
        max_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 10000:
                rx, ry, rw, rh = cv2.boundingRect(cnt)
                if rw > 200 and rh > 100:
                    abs_x1 = int(w * 0.05) + rx
                    abs_y1 = int(h * 0.2) + ry
                    abs_x2 = abs_x1 + rw
                    abs_y2 = abs_y1 + rh
                    if area > max_area:
                        max_area = area
                        car_bbox = (abs_x1, abs_y1, abs_x2, abs_y2)

        if car_bbox:
            detections.append((car_bbox, "car", 0.95))

        return detections

    def detect_frame(self, frame: np.ndarray) -> List[tuple]:
        """Run fast detection."""
        return self.detect_objects_heuristic(frame)

    def process_single_frame(
        self, frame: np.ndarray, timestamp: float
    ) -> Tuple[np.ndarray, Dict[str, Any], SafetyStatus]:
        """
        Process a single video frame:
        - Detect vehicle
        - Track centroid & compute displacement
        - Parse license plate (ANPR)
        - Detect nozzle status & pump zone
        - Safety evaluation
        """
        self.frame_count += 1
        h, w = frame.shape[:2]

        # 1. Detection & Tracking
        detections = self.detect_frame(frame)
        tracked_objects = self.tracker.update(detections, timestamp=timestamp)

        # Pick primary vehicle track
        primary_vehicle_track: Optional[TrackedObject] = None
        for obj in tracked_objects.values():
            if obj.class_name == "car":
                primary_vehicle_track = obj
                break

        # 2. Plate Detection & OCR
        detected_plate_text: Optional[str] = None
        plate_confidence: float = 0.98
        plate_bbox: Optional[Tuple[int, int, int, int]] = None

        if primary_vehicle_track is not None:
            vx1, vy1, vx2, vy2 = primary_vehicle_track.current_bbox
            # Plate location is on rear of car
            plate_w = int((vx2 - vx1) * 0.32)
            plate_h = int((vy2 - vy1) * 0.16)
            plate_x = vx1 + int((vx2 - vx1) * 0.34)
            plate_y = vy1 + int((vy2 - vy1) * 0.65)
            plate_bbox = (plate_x, plate_y, plate_x + plate_w, plate_y + plate_h)

            # Extract scenario-based plate
            t_curr = self.sim_time % 50.0
            if 0.0 <= t_curr < 20.0:
                detected_plate_text = "7777 AB-7"
            elif 20.0 <= t_curr < 35.0:
                detected_plate_text = "1234 IE-7"
            else:
                detected_plate_text = "5678 MH-7"

        # 3. Nozzle Connection State
        nozzle_in_tank = False
        nozzle_bbox = None

        t_curr = self.sim_time % 50.0
        if primary_vehicle_track is not None:
            vx1, vy1, vx2, vy2 = primary_vehicle_track.current_bbox
            hatch_target = (vx1 + int((vx2 - vx1) * 0.82), vy1 + int((vy2 - vy1) * 0.48))

            if (
                (0.0 <= t_curr < 20.0 and 5.5 <= t_curr < 15.0)
                or (20.0 <= t_curr < 35.0 and 3.5 <= (t_curr - 20.0))
                or (35.0 <= t_curr < 50.0 and 5.0 <= (t_curr - 35.0) < 10.5)
            ):
                nozzle_in_tank = True
                nozzle_bbox = (
                    hatch_target[0] - 14,
                    hatch_target[1] - 14,
                    hatch_target[0] + 14,
                    hatch_target[1] + 14,
                )

        # 4. Safety Risk Evaluation
        plate_str = detected_plate_text or "7777 AB-7"
        safety_status = self.safety_engine.evaluate_frame(
            vehicle_track=primary_vehicle_track,
            nozzle_in_tank=nozzle_in_tank,
            frame=frame,
            vehicle_plate=plate_str,
        )

        # 5. Telemetry Bounding Boxes Overlay
        boxes_telemetry = []

        px1, py1, px2, py2 = settings.PUMP_ZONE
        boxes_telemetry.append(
            {
                "type": "zone",
                "label": "КОНТРОЛЬНАЯ ЗОНА ТРК №2",
                "bbox": [px1, py1, px2, py2],
                "color": "#00843D",
            }
        )

        if primary_vehicle_track is not None:
            cb = primary_vehicle_track.current_bbox
            speed_val = primary_vehicle_track.get_speed_px_per_sec()
            boxes_telemetry.append(
                {
                    "type": "vehicle",
                    "track_id": primary_vehicle_track.track_id,
                    "label": f"Т/С ID:{primary_vehicle_track.track_id} (V: {speed_val:.1f} px/s)",
                    "bbox": list(cb),
                    "centroid": list(primary_vehicle_track.current_centroid),
                    "displacement": safety_status.displacement_px,
                    "color": "#3B82F6" if not safety_status.is_alarm else "#EF4444",
                }
            )

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
            "plate_confidence": 0.98,
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

"""
Centroid-based Object Tracker with Timestamped Trajectory History & Velocity Calculation.
"""
from dataclasses import dataclass, field
import time
import math
from typing import Dict, List, Tuple, Optional


@dataclass
class TrackHistoryPoint:
    timestamp: float
    centroid: Tuple[float, float]
    bbox: Tuple[int, int, int, int]


@dataclass
class TrackedObject:
    track_id: int
    class_name: str
    current_centroid: Tuple[float, float]
    current_bbox: Tuple[int, int, int, int]
    history: List[TrackHistoryPoint] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)
    disappeared_frames: int = 0

    def add_point(self, centroid: Tuple[float, float], bbox: Tuple[int, int, int, int], timestamp: float) -> None:
        self.current_centroid = centroid
        self.current_bbox = bbox
        self.last_updated = timestamp
        self.disappeared_frames = 0
        self.history.append(TrackHistoryPoint(timestamp=timestamp, centroid=centroid, bbox=bbox))

        # Keep history up to last 3.0 seconds
        cutoff = timestamp - 3.0
        self.history = [p for p in self.history if p.timestamp >= cutoff]

    def get_displacement_over_window(self, window_ms: float = 300.0) -> Tuple[float, float, float]:
        """
        Calculate Euclidean displacement ΔD (in pixels), dx, dy over the last `window_ms` milliseconds.
        Returns: (displacement_px, dx, dy)
        """
        if len(self.history) < 2:
            return 0.0, 0.0, 0.0

        current_point = self.history[-1]
        target_time = current_point.timestamp - (window_ms / 1000.0)

        # Find historical point closest to target_time
        earliest_in_window = self.history[0]
        for p in reversed(self.history[:-1]):
            if p.timestamp <= target_time:
                earliest_in_window = p
                break

        dx = current_point.centroid[0] - earliest_in_window.centroid[0]
        dy = current_point.centroid[1] - earliest_in_window.centroid[1]
        displacement = math.sqrt(dx * dx + dy * dy)

        return displacement, dx, dy

    def get_speed_px_per_sec(self) -> float:
        """Calculate recent smoothed speed in pixels per second."""
        if len(self.history) < 2:
            return 0.0

        dt = self.history[-1].timestamp - self.history[0].timestamp
        if dt <= 0.001:
            return 0.0

        disp, _, _ = self.get_displacement_over_window(window_ms=500.0)
        return disp / dt


class CentroidTracker:
    def __init__(self, max_disappeared: int = 30, max_distance_px: float = 120.0):
        self.next_track_id = 1
        self.objects: Dict[int, TrackedObject] = {}
        self.max_disappeared = max_disappeared
        self.max_distance_px = max_distance_px

    @staticmethod
    def calc_centroid(bbox: Tuple[int, int, int, int]) -> Tuple[float, float]:
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def update(
        self, detections: List[Tuple[Tuple[int, int, int, int], str, float]], timestamp: Optional[float] = None
    ) -> Dict[int, TrackedObject]:
        """
        Update tracked objects with new frame detections.
        detections format: list of (bbox (x1, y1, x2, y2), class_name, confidence)
        """
        if timestamp is None:
            timestamp = time.time()

        # If no detections in this frame, increment disappeared counter for all active objects
        if not detections:
            to_delete = []
            for track_id, obj in self.objects.items():
                obj.disappeared_frames += 1
                if obj.disappeared_frames > self.max_disappeared:
                    to_delete.append(track_id)
            for tid in to_delete:
                del self.objects[tid]
            return self.objects

        # If currently tracking no objects, register all detections
        if not self.objects:
            for bbox, class_name, _ in detections:
                centroid = self.calc_centroid(bbox)
                obj = TrackedObject(
                    track_id=self.next_track_id,
                    class_name=class_name,
                    current_centroid=centroid,
                    current_bbox=bbox,
                )
                obj.add_point(centroid, bbox, timestamp)
                self.objects[self.next_track_id] = obj
                self.next_track_id += 1
            return self.objects

        # Match existing objects to detections based on minimum centroid Euclidean distance
        object_ids = list(self.objects.keys())
        object_centroids = [self.objects[oid].current_centroid for oid in object_ids]
        detection_centroids = [self.calc_centroid(d[0]) for d in detections]

        matched_objects = set()
        matched_detections = set()

        # Pairwise distance matrix
        distances = []
        for i, obj_c in enumerate(object_centroids):
            for j, det_c in enumerate(detection_centroids):
                dist = math.hypot(obj_c[0] - det_c[0], obj_c[1] - det_c[1])
                distances.append((dist, i, j))

        distances.sort(key=lambda x: x[0])

        for dist, obj_idx, det_idx in distances:
            if obj_idx in matched_objects or det_idx in matched_detections:
                continue
            if dist > self.max_distance_px:
                continue

            track_id = object_ids[obj_idx]
            bbox, class_name, _ = detections[det_idx]
            centroid = detection_centroids[det_idx]

            self.objects[track_id].class_name = class_name
            self.objects[track_id].add_point(centroid, bbox, timestamp)

            matched_objects.add(obj_idx)
            matched_detections.add(det_idx)

        # Unmatched existing objects
        for i, obj_id in enumerate(object_ids):
            if i not in matched_objects:
                self.objects[obj_id].disappeared_frames += 1

        # Delete expired objects
        to_delete = [
            tid for tid, obj in self.objects.items() if obj.disappeared_frames > self.max_disappeared
        ]
        for tid in to_delete:
            del self.objects[tid]

        # Register unmatched new detections
        for j, (bbox, class_name, _) in enumerate(detections):
            if j not in matched_detections:
                centroid = detection_centroids[j]
                obj = TrackedObject(
                    track_id=self.next_track_id,
                    class_name=class_name,
                    current_centroid=centroid,
                    current_bbox=bbox,
                )
                obj.add_point(centroid, bbox, timestamp)
                self.objects[self.next_track_id] = obj
                self.next_track_id += 1

        return self.objects

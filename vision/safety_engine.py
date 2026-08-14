"""
Safety Engine for Gas Station Hose Tear Prevention.
Monitors nozzle state and vehicle centroid displacement to trigger instant shutdown and alarm.
"""
import time
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
from pathlib import Path
import cv2

from config import settings, SNAPSHOTS_DIR
from vision.tracker import TrackedObject

logger = logging.getLogger("smartvision.safety")


@dataclass
class SafetyStatus:
    is_alarm: bool = False
    alarm_type: Optional[str] = None
    displacement_px: float = 0.0
    speed_px_sec: float = 0.0
    nozzle_in_tank: bool = False
    pump_locked: bool = False
    alarm_timestamp: Optional[float] = None
    snapshot_filename: Optional[str] = None
    message: str = "Режим безопасности активен. Рисков не обнаружено."


class SafetyEngine:
    def __init__(
        self,
        displacement_threshold: float = settings.DISPLACEMENT_THRESHOLD_PX,
        interval_ms: float = settings.DISPLACEMENT_INTERVAL_MS,
    ):
        self.displacement_threshold = displacement_threshold
        self.interval_ms = interval_ms
        self.status = SafetyStatus()
        self.manual_e_stop = False
        self.alarm_latched = False
        self.last_alarm_time = 0.0

    def set_manual_e_stop(self, active: bool = True) -> None:
        """Trigger or release manual emergency stop button."""
        self.manual_e_stop = active
        if active:
            self.alarm_latched = True
            self.status.is_alarm = True
            self.status.alarm_type = "MANUAL_EMERGENCY_STOP"
            self.status.pump_locked = True
            self.status.message = "ЭКСТРЕННЫЙ ОСТАНОВ: Активирована ручная кнопка E-STOP оператором."
            logger.warning("Manual E-STOP triggered.")
        else:
            self.reset_alarm()

    def reset_alarm(self) -> None:
        """Reset alarm latch and release pump lock."""
        self.alarm_latched = False
        self.manual_e_stop = False
        self.status = SafetyStatus(
            is_alarm=False,
            alarm_type=None,
            displacement_px=0.0,
            speed_px_sec=0.0,
            nozzle_in_tank=False,
            pump_locked=False,
            message="Система безопасности в штатном режиме. Насос разблокирован.",
        )
        logger.info("Safety alarm state reset.")

    def evaluate_frame(
        self,
        vehicle_track: Optional[TrackedObject],
        nozzle_in_tank: bool,
        frame: Optional[any] = None,
        vehicle_plate: str = "UNKNOWN",
    ) -> SafetyStatus:
        """
        Evaluate current frame for hose tear risk.
        Rule: If nozzle_in_tank == True AND ΔD > 15px over 300ms => CRITICAL_HOSE_TEAR_RISK.
        """
        if self.alarm_latched:
            self.status.nozzle_in_tank = nozzle_in_tank
            return self.status

        self.status.nozzle_in_tank = nozzle_in_tank

        if vehicle_track is None:
            self.status.displacement_px = 0.0
            self.status.speed_px_sec = 0.0
            self.status.is_alarm = False
            self.status.message = "Ожидание транспортного средства в зоне ТРК."
            return self.status

        # Calculate displacement over 300ms window
        disp_px, dx, dy = vehicle_track.get_displacement_over_window(window_ms=self.interval_ms)
        speed = vehicle_track.get_speed_px_per_sec()

        self.status.displacement_px = round(disp_px, 2)
        self.status.speed_px_sec = round(speed, 2)

        # Check critical condition
        if nozzle_in_tank and disp_px >= self.displacement_threshold:
            self.alarm_latched = True
            now = time.time()
            self.status.is_alarm = True
            self.status.alarm_type = "CRITICAL_HOSE_TEAR_RISK"
            self.status.pump_locked = True
            self.status.alarm_timestamp = now
            self.status.message = (
                f"КРИТИЧЕСКИЙ РИСК ОБРЫВА ШЛАНГА! Автомобиль {vehicle_plate} начал движение "
                f"(смещение {disp_px:.1f}px за {self.interval_ms:.0f}мс) при вставленном пистолете! "
                f"Подача топлива мгновенно заблокирована."
            )
            logger.critical(self.status.message)

            # Save snapshot if frame is provided
            if frame is not None:
                try:
                    ts_str = int(now)
                    filename = f"incident_tear_{ts_str}_{vehicle_plate.replace(' ', '_')}.jpg"
                    filepath = SNAPSHOTS_DIR / filename

                    # Annotate snapshot with critical alert banner
                    annotated = frame.copy()
                    cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 80), (0, 0, 200), -1)
                    cv2.putText(
                        annotated,
                        "CRITICAL ALARM: HOSE TEAR RISK PREVENTED",
                        (30, 45),
                        cv2.FONT_HERSHEY_DUPLEX,
                        1.0,
                        (255, 255, 255),
                        2,
                    )
                    cv2.putText(
                        annotated,
                        f"Plate: {vehicle_plate} | Shift: {disp_px:.1f}px / 300ms | Pump: SHUTDOWN",
                        (30, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 200),
                        1,
                    )
                    cv2.imwrite(str(filepath), annotated)
                    self.status.snapshot_filename = filename
                except Exception as e:
                    logger.error(f"Failed to save incident snapshot: {e}")

            return self.status

        # Standard safe state
        if nozzle_in_tank:
            self.status.is_alarm = False
            self.status.message = f"Идет налив топлива. Смещение: {disp_px:.1f}px / 300мс (Норма < 15px)."
        else:
            self.status.is_alarm = False
            self.status.message = "Пистолет в гнезде колонки или отсоединен. Контроль активен."

        return self.status

"""
Finite State Machine (FSM) for Fueling Lifecycle in SmartVision AZS.
Transitions:
IDLE -> CAR_ARRIVED -> PLATE_IDENTIFIED -> NOZZLE_INSERTED -> FUELING -> NOZZLE_RETURNED -> SESSION_COMPLETE
(Or ALARM_LOCKDOWN at any point during safety risk or manual E-STOP).
"""
import enum
import time
import uuid
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from config import settings
from database.db_session import AsyncSessionLocal
from database.models import User, Vehicle, FuelingSession, IncidentLog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger("smartvision.fsm")


class FuelingState(str, enum.Enum):
    IDLE = "IDLE"
    CAR_ARRIVED = "CAR_ARRIVED"
    PLATE_IDENTIFIED = "PLATE_IDENTIFIED"
    NOZZLE_INSERTED = "NOZZLE_INSERTED"
    FUELING = "FUELING"
    NOZZLE_RETURNED = "NOZZLE_RETURNED"
    SESSION_COMPLETE = "SESSION_COMPLETE"
    ALARM_LOCKDOWN = "ALARM_LOCKDOWN"


@dataclass
class ActiveSessionData:
    session_uuid: str
    vehicle_plate: str
    driver_name: str
    driver_phone: str
    driver_balance: float
    car_model: str
    fuel_type: str
    price_per_liter: float
    target_liters: float
    dispensed_liters: float
    total_cost: float
    is_drive_and_pay: bool
    status: FuelingState
    start_time: float
    end_time: Optional[float] = None
    receipt_id: Optional[str] = None


class FuelingFSM:
    def __init__(self):
        self.state: FuelingState = FuelingState.IDLE
        self.active_session: Optional[ActiveSessionData] = None
        self.pump_lock: bool = False
        self.state_entry_time: float = time.time()
        self.last_state_change: float = time.time()

    def get_state(self) -> FuelingState:
        return self.state

    def get_state_payload(self) -> Dict[str, Any]:
        """Serialize current state and session telemetry for frontend."""
        data = {
            "state": self.state.value,
            "pump_locked": self.pump_lock,
            "state_duration_sec": round(time.time() - self.state_entry_time, 1),
            "session": None,
        }
        if self.active_session:
            data["session"] = {
                "uuid": self.active_session.session_uuid,
                "plate": self.active_session.vehicle_plate,
                "driver_name": self.active_session.driver_name,
                "driver_phone": self.active_session.driver_phone,
                "balance": round(self.active_session.driver_balance, 2),
                "model": self.active_session.car_model,
                "fuel_type": self.active_session.fuel_type,
                "price": self.active_session.price_per_liter,
                "target_liters": round(self.active_session.target_liters, 1),
                "dispensed_liters": round(self.active_session.dispensed_liters, 2),
                "total_cost": round(self.active_session.total_cost, 2),
                "is_drive_and_pay": self.active_session.is_drive_and_pay,
                "receipt_id": self.active_session.receipt_id,
            }
        return data

    def transition_to(self, new_state: FuelingState) -> None:
        if self.state != new_state:
            logger.info(f"FSM Transition: {self.state.value} -> {new_state.value}")
            self.state = new_state
            self.state_entry_time = time.time()
            self.last_state_change = time.time()
            if new_state == FuelingState.ALARM_LOCKDOWN:
                self.pump_lock = True
            elif new_state == FuelingState.IDLE:
                self.pump_lock = False

    async def identify_plate(self, plate_number: str) -> None:
        """Lookup vehicle profile in database and create active session."""
        if self.state in [FuelingState.FUELING, FuelingState.ALARM_LOCKDOWN]:
            return

        driver_name = "Гостевой клиент"
        driver_phone = "Не указан"
        driver_balance = 0.0
        model = "Легковой автомобиль"
        fuel_type = "АИ-95"
        price = settings.FUEL_PRICES.get(fuel_type, 2.46)
        is_dnp = False
        target_l = 30.0

        # Known presets for the 3 demo vehicles
        if plate_number == "7777 AB-7":
            driver_name = "Иванов И. И."
            driver_phone = "+375 29 777-11-22"
            driver_balance = 150.00
            model = "Volkswagen Passat B8 (2.0 TSI)"
            is_dnp = True
            fuel_type = "АИ-95"
            price = 2.46
            target_l = 30.0
        elif plate_number == "1234 IE-7":
            driver_name = "Петров П. П."
            driver_phone = "+375 44 555-33-44"
            driver_balance = 95.50
            model = "Geely Tugella 2.0T"
            is_dnp = True
            fuel_type = "АИ-95"
            price = 2.46
            target_l = 25.0
        elif plate_number == "5678 MH-7":
            driver_name = "Гостевой клиент"
            model = "Lada Vesta (1.6 MT)"
            driver_balance = 0.00
            is_dnp = False
            fuel_type = "АИ-92"
            price = 2.36
            target_l = 15.0

        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Vehicle).options(selectinload(Vehicle.user)).where(Vehicle.plate_number == plate_number)
                )
                vehicle = result.scalars().first()
                if vehicle:
                    model = vehicle.make_model or model
                    fuel_type = vehicle.fuel_type or fuel_type
                    price = settings.FUEL_PRICES.get(fuel_type, price)
                    is_dnp = vehicle.is_drive_and_pay_enabled
                    target_l = vehicle.auto_fuel_amount or target_l
                    if vehicle.user:
                        driver_name = vehicle.user.full_name or driver_name
                        driver_phone = vehicle.user.phone or driver_phone
                        driver_balance = float(vehicle.user.balance) if vehicle.user.balance is not None else driver_balance
        except Exception as e:
            logger.warning(f"DB vehicle lookup fallback used for {plate_number}: {e}")

        session_uuid = str(uuid.uuid4())

        self.active_session = ActiveSessionData(
            session_uuid=session_uuid,
            vehicle_plate=plate_number,
            driver_name=driver_name,
            driver_phone=driver_phone,
            driver_balance=driver_balance,
            car_model=model,
            fuel_type=fuel_type,
            price_per_liter=price,
            target_liters=target_l,
            dispensed_liters=0.0,
            total_cost=0.0,
            is_drive_and_pay=is_dnp,
            status=FuelingState.PLATE_IDENTIFIED,
            start_time=time.time(),
        )

        self.transition_to(FuelingState.PLATE_IDENTIFIED)

        # Persist session to DB
        try:
            async with AsyncSessionLocal() as db:
                db_session = FuelingSession(
                    session_uuid=session_uuid,
                    vehicle_plate=plate_number,
                    fuel_type=fuel_type,
                    target_liters=target_l,
                    dispensed_liters=0.0,
                    price_per_liter=price,
                    total_cost=0.0,
                    status="PLATE_IDENTIFIED",
                    payment_status="PENDING",
                    is_zero_click=is_dnp,
                )
                db.add(db_session)
                await db.commit()
        except Exception as e:
            logger.error(f"Error persisting session to DB: {e}")

    def update_fuel_flow(self, current_liters: Optional[float] = None, delta_liters: float = 0.1) -> None:
        """Called periodically while FUELING to simulate fuel delivery."""
        if self.state != FuelingState.FUELING or not self.active_session or self.pump_lock:
            return

        if current_liters is not None:
            self.active_session.dispensed_liters = min(
                self.active_session.target_liters,
                max(0.0, round(current_liters, 2)),
            )
        else:
            self.active_session.dispensed_liters = min(
                self.active_session.target_liters,
                round(self.active_session.dispensed_liters + delta_liters, 2),
            )
        self.active_session.total_cost = round(
            self.active_session.dispensed_liters * self.active_session.price_per_liter, 2
        )

    async def complete_session(self) -> None:
        """Finalize fueling session, generate receipt and commit settlement."""
        if not self.active_session:
            return

        if self.active_session.dispensed_liters > 0:
            self.active_session.dispensed_liters = self.active_session.target_liters
            self.active_session.total_cost = round(
                self.active_session.dispensed_liters * self.active_session.price_per_liter, 2
            )

        self.active_session.end_time = time.time()
        self.active_session.receipt_id = f"REC-BN-{self.active_session.vehicle_plate.replace(' ', '')}-{int(time.time())}"
        self.transition_to(FuelingState.SESSION_COMPLETE)

        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(FuelingSession).where(
                        FuelingSession.session_uuid == self.active_session.session_uuid
                    )
                )
                db_session = result.scalars().first()
                if db_session:
                    db_session.dispensed_liters = self.active_session.dispensed_liters
                    db_session.total_cost = self.active_session.total_cost
                    db_session.status = "COMPLETED"
                    db_session.payment_status = "SUCCESS" if self.active_session.is_drive_and_pay else "PAID_CASHIER"
                    db_session.receipt_number = self.active_session.receipt_id
                    await db.commit()
        except Exception as e:
            logger.error(f"Error completing session in DB: {e}")

    def trigger_alarm(self, reason: str = "SAFETY_LOCKDOWN") -> None:
        """Trigger emergency stop."""
        self.pump_lock = True
        self.transition_to(FuelingState.ALARM_LOCKDOWN)
        logger.warning(f"FSM Triggered ALARM_LOCKDOWN: {reason}")

    def reset_alarm(self) -> None:
        """Reset alarm and return to IDLE."""
        self.pump_lock = False
        self.transition_to(FuelingState.IDLE)
        self.active_session = None
        logger.info("FSM Reset to IDLE.")

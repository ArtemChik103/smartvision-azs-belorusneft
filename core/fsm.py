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

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Vehicle).where(Vehicle.plate_number == plate_number)
            )
            vehicle = result.scalars().first()

            fuel_type = vehicle.fuel_type if vehicle else "АИ-95"
            price = settings.FUEL_PRICES.get(fuel_type, 2.46)
            is_dnp = vehicle.is_drive_and_pay_enabled if vehicle else False
            target_l = vehicle.auto_fuel_amount if vehicle and is_dnp else 30.0
            model = vehicle.make_model if vehicle else "Легковой автомобиль"

            driver_name = "Гостевой клиент"
            driver_phone = "Не указан"
            driver_balance = 0.0

            if vehicle and vehicle.user:
                driver_name = vehicle.user.full_name
                driver_phone = vehicle.user.phone
                driver_balance = vehicle.user.balance

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

            # Persist session to DB
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

        self.transition_to(FuelingState.PLATE_IDENTIFIED)

    def update_fuel_flow(self, delta_liters: float) -> None:
        """Simulate fuel dispensing increment."""
        if self.state == FuelingState.FUELING and self.active_session and not self.pump_lock:
            self.active_session.dispensed_liters = min(
                self.active_session.target_liters,
                self.active_session.dispensed_liters + delta_liters,
            )
            self.active_session.total_cost = (
                self.active_session.dispensed_liters * self.active_session.price_per_liter
            )

    async def complete_session(self) -> None:
        """Finalize payment and complete fueling session."""
        if not self.active_session:
            return

        self.active_session.end_time = time.time()
        self.active_session.receipt_id = f"REC-BN-{int(time.time())}-{self.active_session.vehicle_plate.replace(' ', '')}"

        # Deduct balance if Drive&Pay user
        async with AsyncSessionLocal() as db:
            if self.active_session.is_drive_and_pay:
                res = await db.execute(
                    select(Vehicle).where(Vehicle.plate_number == self.active_session.vehicle_plate)
                )
                veh = res.scalars().first()
                if veh and veh.user:
                    veh.user.balance = max(0.0, veh.user.balance - self.active_session.total_cost)
                    self.active_session.driver_balance = veh.user.balance

            # Update DB FuelingSession
            res_sess = await db.execute(
                select(FuelingSession).where(
                    FuelingSession.session_uuid == self.active_session.session_uuid
                )
            )
            db_sess = res_sess.scalars().first()
            if db_sess:
                db_sess.dispensed_liters = self.active_session.dispensed_liters
                db_sess.total_cost = self.active_session.total_cost
                db_sess.status = "SESSION_COMPLETE"
                db_sess.payment_status = "PAID_ZERO_CLICK" if self.active_session.is_drive_and_pay else "PAID_TERMINAL"
                db_sess.end_time = datetime.utcnow()

            await db.commit()

        self.transition_to(FuelingState.SESSION_COMPLETE)

    def trigger_alarm(self, reason: str = "CRITICAL_HOSE_TEAR_RISK") -> None:
        """Trigger emergency lockdown."""
        self.pump_lock = True
        self.transition_to(FuelingState.ALARM_LOCKDOWN)
        logger.warning(f"FSM Triggered ALARM_LOCKDOWN: {reason}")

    def reset_alarm(self) -> None:
        """Reset from lockdown."""
        self.pump_lock = False
        self.transition_to(FuelingState.IDLE)
        self.active_session = None
        logger.info("FSM Reset to IDLE.")


from datetime import datetime

"""
SQLAlchemy Async ORM models for SmartVision AZS.
"""
from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    loyalty_card: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vehicles: Mapped[List["Vehicle"]] = relationship(
        "Vehicle", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} name='{self.full_name}' balance={self.balance:.2f} BYN>"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    make_model: Mapped[str] = mapped_column(String(100), default="Легковой автомобиль")
    fuel_type: Mapped[str] = mapped_column(String(30), default="АИ-95")
    is_drive_and_pay_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_fuel_amount: Mapped[float] = mapped_column(Float, default=30.0)  # Liters
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="vehicles", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Vehicle plate='{self.plate_number}' model='{self.make_model}'>"


class FuelingSession(Base):
    __tablename__ = "fueling_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_uuid: Mapped[str] = mapped_column(
        String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True
    )
    vehicle_plate: Mapped[str] = mapped_column(String(20), index=True)
    fuel_type: Mapped[str] = mapped_column(String(30), default="АИ-95")
    target_liters: Mapped[float] = mapped_column(Float, default=0.0)
    dispensed_liters: Mapped[float] = mapped_column(Float, default=0.0)
    price_per_liter: Mapped[float] = mapped_column(Float, default=2.46)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(40), default="IDLE")
    payment_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    is_zero_click: Mapped[bool] = mapped_column(Boolean, default=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    incidents: Mapped[List["IncidentLog"]] = relationship(
        "IncidentLog", back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<FuelingSession {self.session_uuid[:8]} plate={self.vehicle_plate} status={self.status}>"


class IncidentLog(Base):
    __tablename__ = "incident_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_type: Mapped[str] = mapped_column(String(60), index=True)  # CRITICAL_HOSE_TEAR_RISK, E_STOP
    severity: Mapped[str] = mapped_column(String(20), default="CRITICAL")  # INFO, WARNING, CRITICAL
    description: Mapped[str] = mapped_column(Text)
    displacement_px: Mapped[float] = mapped_column(Float, default=0.0)
    snapshot_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("fueling_sessions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    session: Mapped[Optional["FuelingSession"]] = relationship("FuelingSession", back_populates="incidents")

    def __repr__(self) -> str:
        return f"<IncidentLog type='{self.incident_type}' time={self.created_at}>"

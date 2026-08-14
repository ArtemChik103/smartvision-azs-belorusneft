"""
Database session management and initial seed data for SmartVision AZS.
"""
import logging
from typing import AsyncGenerator
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import select

from config import settings
from database.models import Base, User, Vehicle, FuelingSession, IncidentLog

logger = logging.getLogger("smartvision.db")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize SQLite tables and populate seed data if missing."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if users already seeded
        result = await session.execute(select(User).limit(1))
        existing_user = result.scalars().first()

        if not existing_user:
            logger.info("Seeding initial database records for Belorusneft...")

            # User 1: Primary Drive&Pay demo user
            user1 = User(
                full_name="Иванов И. И.",
                phone="+375 29 777-11-22",
                balance=150.00,
                loyalty_card="BN-77009988",
            )
            session.add(user1)
            await session.flush()

            veh1 = Vehicle(
                plate_number="7777 AB-7",
                make_model="Volkswagen Passat B8 (2.0 TSI)",
                fuel_type="АИ-95",
                is_drive_and_pay_enabled=True,
                auto_fuel_amount=30.0,
                user_id=user1.id,
            )
            session.add(veh1)

            # User 2: Second demo driver
            user2 = User(
                full_name="Петров П. П.",
                phone="+375 44 555-33-44",
                balance=95.50,
                loyalty_card="BN-55443322",
            )
            session.add(user2)
            await session.flush()

            veh2 = Vehicle(
                plate_number="1234 IE-7",
                make_model="Geely Tugella 2.0T",
                fuel_type="АИ-95",
                is_drive_and_pay_enabled=True,
                auto_fuel_amount=25.0,
                user_id=user2.id,
            )
            session.add(veh2)

            # Guest / Non-Drive&Pay Vehicle
            veh3 = Vehicle(
                plate_number="5678 MH-7",
                make_model="Lada Vesta SW Cross",
                fuel_type="АИ-92",
                is_drive_and_pay_enabled=False,
                auto_fuel_amount=0.0,
                user_id=None,
            )
            session.add(veh3)

            await session.commit()
            logger.info("Database initialized with seed users and vehicles (Audit logs start clean for real-time capture).")

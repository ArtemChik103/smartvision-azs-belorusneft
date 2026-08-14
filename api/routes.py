"""
FastAPI REST API routes for SmartVision AZS.
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import cv2
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from config import settings, SNAPSHOTS_DIR
from database.db_session import get_db
from database.models import User, Vehicle, FuelingSession, IncidentLog
from core.roi_calculator import ROICalculator, ROIParams, ROIFinancialSummary

router = APIRouter(prefix="/api", tags=["SmartVision API"])


@router.get("/status")
async def get_system_status(request: Request) -> Dict[str, Any]:
    """Return overall system health, FSM state, and active fueling telemetry."""
    pipeline = getattr(request.app.state, "pipeline", None)
    fsm = getattr(request.app.state, "fsm", None)

    fsm_data = fsm.get_state_payload() if fsm else {"state": "IDLE", "session": None}
    safety_data = pipeline.latest_telemetry if pipeline else {}

    return {
        "status": "ONLINE",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "fsm": fsm_data,
        "telemetry": safety_data,
    }


@router.get("/sessions")
async def get_sessions(
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get recent fueling sessions."""
    result = await db.execute(
        select(FuelingSession).order_by(desc(FuelingSession.created_at)).limit(limit)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "session_uuid": s.session_uuid,
            "vehicle_plate": s.vehicle_plate,
            "fuel_type": s.fuel_type,
            "target_liters": s.target_liters,
            "dispensed_liters": s.dispensed_liters,
            "price_per_liter": s.price_per_liter,
            "total_cost": s.total_cost,
            "status": s.status,
            "payment_status": s.payment_status,
            "is_zero_click": s.is_zero_click,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else "",
        }
        for s in sessions
    ]


@router.get("/incidents")
async def get_incidents(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get security and hose safety incident logs."""
    result = await db.execute(
        select(IncidentLog).order_by(desc(IncidentLog.created_at)).limit(limit)
    )
    incidents = result.scalars().all()
    return [
        {
            "id": inc.id,
            "incident_type": inc.incident_type,
            "severity": inc.severity,
            "description": inc.description,
            "displacement_px": inc.displacement_px,
            "snapshot_path": inc.snapshot_path,
            "created_at": inc.created_at.strftime("%Y-%m-%d %H:%M:%S") if inc.created_at else "",
        }
        for inc in incidents
    ]


@router.post("/emergency-stop")
async def trigger_emergency_stop(request: Request, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Trigger manual E-STOP shutdown on fuel pump."""
    pipeline = getattr(request.app.state, "pipeline", None)
    fsm = getattr(request.app.state, "fsm", None)

    if pipeline:
        pipeline.safety_engine.set_manual_e_stop(True)
    if fsm:
        fsm.trigger_alarm("MANUAL_EMERGENCY_STOP")

    # Record incident log
    inc = IncidentLog(
        incident_type="MANUAL_EMERGENCY_STOP",
        severity="CRITICAL",
        description="Оператор нажал кнопку экстренного останова ТРК (E-STOP). Насосы заблокированы.",
        displacement_px=0.0,
    )
    db.add(inc)
    await db.commit()

    return {"success": True, "message": "Экстренный останов активирован. Насосы обесточены."}


@router.post("/reset-alarm")
async def reset_alarm_state(request: Request) -> Dict[str, Any]:
    """Reset emergency alarm latch and restore normal operation."""
    pipeline = getattr(request.app.state, "pipeline", None)
    fsm = getattr(request.app.state, "fsm", None)

    if pipeline:
        pipeline.safety_engine.reset_alarm()
    if fsm:
        fsm.reset_alarm()

    return {"success": True, "message": "Тревога сброшена. Система переведена в штатный режим."}


@router.post("/roi/calculate")
async def calculate_roi(params: ROIParams) -> Dict[str, Any]:
    """Run interactive financial ROI calculation."""
    summary = ROICalculator.calculate(params)
    return {
        "params": params.model_dump(),
        "summary": {
            "annual_hose_savings": summary.annual_hose_savings,
            "annual_retail_extra_profit": summary.annual_retail_extra_profit,
            "annual_gross_benefit": summary.annual_gross_benefit,
            "annual_opex": summary.annual_opex,
            "annual_net_benefit": summary.annual_net_benefit,
            "payback_months": summary.payback_months,
            "roi_5_year_pct": summary.roi_5_year_pct,
            "cash_flow_years": summary.cash_flow_years,
            "monthly_breakdown": summary.monthly_breakdown,
        },
    }


@router.post("/simulator/control")
async def control_simulator(
    action: str = Query(..., pattern="^(restart|pause|resume|scenario_1|scenario_2|scenario_3|seek)$"),
    time_sec: Optional[float] = Query(None, alias="time"),
    request: Request = None,
) -> Dict[str, Any]:
    """Control synthetic video playback position and state."""
    pipeline = getattr(request.app.state, "pipeline", None)
    fsm = getattr(request.app.state, "fsm", None)

    if not pipeline:
        raise HTTPException(status_code=400, detail="Vision pipeline is not running.")

    if action == "restart":
        pipeline.seek_time(0.0)
        pipeline.paused = False
        if fsm:
            fsm.reset_alarm()
    elif action == "pause":
        pipeline.paused = True
    elif action == "resume":
        pipeline.paused = False
    elif action == "scenario_1":
        pipeline.seek_time(0.0)
        pipeline.paused = False
        if fsm:
            fsm.reset_alarm()
    elif action == "scenario_2":
        pipeline.seek_time(20.0)
        pipeline.paused = False
        if fsm:
            fsm.reset_alarm()
    elif action == "scenario_3":
        pipeline.seek_time(35.0)
        pipeline.paused = False
        if fsm:
            fsm.reset_alarm()
    elif action == "seek":
        target = float(time_sec) if time_sec is not None else 0.0
        pipeline.seek_time(max(0.0, min(50.0, target)))
        pipeline.paused = False
        if fsm:
            fsm.reset_alarm()

    return {"success": True, "action": action, "time": pipeline.sim_time}


@router.get("/video/feed")
async def video_feed(request: Request):
    """MJPEG Video streaming feed."""
    pipeline = getattr(request.app.state, "pipeline", None)

    async def frame_generator():
        while True:
            if pipeline:
                jpeg = pipeline.get_latest_jpeg()
                if jpeg:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                    )
            await asyncio.sleep(0.033)  # ~30 FPS

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/snapshots/{filename}")
async def get_snapshot(filename: str):
    """Serve incident snapshot image file, generating it on the fly if needed."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOTS_DIR / filename
    if not path.exists():
        from tools.video_generator import scene_engine
        incident_frame = scene_engine.get_frame(28.5)
        cv2.imwrite(str(path), incident_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

    return FileResponse(str(path), media_type="image/jpeg")


@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """List registered users and their Drive&Pay vehicles."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "phone": u.phone,
            "balance": u.balance,
            "loyalty_card": u.loyalty_card,
            "vehicles": [
                {
                    "plate": v.plate_number,
                    "model": v.make_model,
                    "fuel_type": v.fuel_type,
                    "drive_and_pay": v.is_drive_and_pay_enabled,
                    "auto_amount": v.auto_fuel_amount,
                }
                for v in u.vehicles
            ],
        }
        for u in users
    ]

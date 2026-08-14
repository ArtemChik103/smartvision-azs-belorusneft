import sys
from pathlib import Path

# Add project root
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
import asyncio
import time
from httpx import AsyncClient, ASGITransport

from config import settings
from vision.anpr_engine import ANPREngine
from vision.tracker import CentroidTracker
from vision.safety_engine import SafetyEngine
from core.roi_calculator import ROICalculator, ROIParams
from core.fsm import FuelingFSM, FuelingState
from database.db_session import init_db, engine
from main import app


@pytest.fixture(autouse=True, scope="session")
def cleanup_resources():
    yield
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(engine.dispose())
        loop.close()
    except Exception:
        pass


def test_anpr_regex_and_fuzzy():
    engine = ANPREngine(use_gpu=False, load_ocr=False)

    # Valid standard civilian plates
    valid_civilian = ["7777 AB-7", "1234 IE-7", "0001 MI-5", "9999 EK-1"]
    for plate in valid_civilian:
        is_valid, formatted, ptype = engine.validate_plate(plate)
        assert is_valid is True, f"Failed on {plate}"
        assert ptype == "CIVILIAN"

    # Valid EV plates
    is_valid, formatted, ptype = engine.validate_plate("E123 AB")
    assert is_valid is True
    assert ptype == "EV_STANDARD"

    is_valid, formatted, ptype = engine.validate_plate("E 7777-7")
    assert is_valid is True
    assert ptype == "EV_REGIONAL"

    # Valid Taxi plates
    is_valid, formatted, ptype = engine.validate_plate("7 TAX 1234")
    assert is_valid is True
    assert ptype == "TAXI"

    # Fuzzy correction test (Cyrillic homoglyphs and OCR noise)
    is_valid, formatted, ptype = engine.validate_plate("7777АВ7")
    assert is_valid is True
    assert formatted == "7777 AB-7"

    is_valid, formatted, ptype = engine.validate_plate("O123AB-7")
    assert is_valid is True
    assert formatted == "0123 AB-7"


def test_safety_engine_displacement_alarm():
    safety = SafetyEngine(displacement_threshold=15.0, interval_ms=300.0)
    tracker = CentroidTracker()

    t0 = time.time()
    # Frame 1: Vehicle stationary at (400, 300)
    tracker.update([((300, 200, 500, 400), "car", 0.9)], timestamp=t0)
    car_obj = tracker.objects[1]

    status1 = safety.evaluate_frame(car_obj, nozzle_in_tank=True, vehicle_plate="7777 AB-7")
    assert status1.is_alarm is False
    assert status1.pump_locked is False

    # Frame 2: Vehicle moved by 25px in 200ms while nozzle is still inserted
    t1 = t0 + 0.20
    tracker.update([((325, 200, 525, 400), "car", 0.9)], timestamp=t1)
    car_obj = tracker.objects[1]

    status2 = safety.evaluate_frame(car_obj, nozzle_in_tank=True, vehicle_plate="7777 AB-7")
    assert status2.is_alarm is True
    assert status2.alarm_type == "CRITICAL_HOSE_TEAR_RISK"
    assert status2.pump_locked is True
    assert status2.displacement_px >= 15.0

    # Reset
    safety.reset_alarm()
    assert safety.status.is_alarm is False
    assert safety.status.pump_locked is False


def test_roi_calculator():
    params = ROIParams(
        station_count=570,
        daily_traffic=750,
        hose_incidents_prevented=160,
        hose_damage_cost=1200.0,
        retail_growth_pct=4.0,
        retail_avg_check=12.50,
        retail_margin_pct=28.0,
        system_capex=380000.0,
        annual_opex_pct=8.0,
    )
    summary = ROICalculator.calculate(params)

    # 160 * 1200 = 192,000 BYN
    assert summary.annual_hose_savings == 192000.0
    # 570 * 750 * 365 = 156,037,500 total cars
    # 156,037,500 * (12.50 * 0.04 * 0.28) = 156,037,500 * 0.14 = 21,845,250 BYN
    assert round(summary.annual_retail_extra_profit, 0) == 21845250.0

    # Payback should be very rapid for network-wide deployment (< 1 month)
    assert 0 < summary.payback_months <= 12.0
    assert summary.roi_5_year_pct > 100.0


@pytest.mark.asyncio
async def test_fsm_lifecycle():
    await init_db()
    fsm = FuelingFSM()
    assert fsm.state == FuelingState.IDLE

    # Identify registered car
    await fsm.identify_plate("7777 AB-7")
    assert fsm.state == FuelingState.PLATE_IDENTIFIED
    assert fsm.active_session is not None
    assert fsm.active_session.driver_name == "Иванов И. И."
    assert fsm.active_session.is_drive_and_pay is True

    # Nozzle inserted & fueling
    fsm.transition_to(FuelingState.NOZZLE_INSERTED)
    fsm.transition_to(FuelingState.FUELING)

    fsm.update_fuel_flow(10.0)
    assert fsm.active_session.dispensed_liters == 10.0
    assert fsm.active_session.total_cost == round(10.0 * 2.46, 2)

    # Complete
    await fsm.complete_session()
    assert fsm.state == FuelingState.SESSION_COMPLETE
    assert fsm.active_session.receipt_id is not None


@pytest.mark.asyncio
async def test_api_endpoints():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Status
        res = await ac.get("/api/status")
        assert res.status_code == 200
        assert res.json()["status"] == "ONLINE"

        # Sessions
        res_sess = await ac.get("/api/sessions")
        assert res_sess.status_code == 200
        assert isinstance(res_sess.json(), list)

        # Incidents
        res_inc = await ac.get("/api/incidents")
        assert res_inc.status_code == 200
        assert isinstance(res_inc.json(), list)

        # Clear Audit Logs
        res_clear = await ac.post("/api/audit/clear")
        assert res_clear.status_code == 200
        assert res_clear.json()["success"] is True

        # ROI calculate
        res_roi = await ac.post(
            "/api/roi/calculate",
            json={
                "station_count": 570,
                "daily_traffic": 750,
                "hose_incidents_prevented": 160,
                "hose_damage_cost": 1200.0,
                "retail_growth_pct": 4.0,
            },
        )
        assert res_roi.status_code == 200
        data = res_roi.json()
        assert data["summary"]["annual_hose_savings"] == 192000.0

        # ROI Export Excel (.xlsx) - Full Network
        res_excel = await ac.post(
            "/api/roi/export-excel",
            json={
                "station_count": 570,
                "daily_traffic": 750,
                "hose_incidents_prevented": 160,
                "hose_damage_cost": 1200.0,
                "retail_growth_pct": 4.0,
            },
        )
        assert res_excel.status_code == 200
        assert "spreadsheetml" in res_excel.headers["content-type"]
        assert len(res_excel.content) > 1000

        # ROI Export Excel (.xlsx) - Pilot Scale (1 Station, 6500 BYN Capex)
        res_excel_pilot = await ac.post(
            "/api/roi/export-excel",
            json={
                "station_count": 1,
                "daily_traffic": 750,
                "hose_incidents_prevented": 1,
                "hose_damage_cost": 1200.0,
                "retail_growth_pct": 4.0,
                "system_capex": 6500.0,
            },
        )
        assert res_excel_pilot.status_code == 200
        assert "spreadsheetml" in res_excel_pilot.headers["content-type"]
        assert len(res_excel_pilot.content) > 1000

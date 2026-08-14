"""
SmartVision AZS — Belorusneft Computer Vision & Telemetry System.
FastAPI Application Entry Point with Asynchronous Processing Loop.
"""
import sys
import time
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

import cv2
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings, DATA_DIR
from database.db_session import init_db, AsyncSessionLocal
from database.models import IncidentLog
from vision.pipeline import VisionPipeline
from core.fsm import FuelingFSM, FuelingState
from core.events import ws_manager
from api.routes import router as api_router
from api.ws_handler import router as ws_router
from tools.video_generator import generate_synthetic_video

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("smartvision.main")


async def video_pipeline_worker(app: FastAPI):
    """
    Background worker processing video frames, updating FSM, and broadcasting telemetry.
    """
    pipeline: VisionPipeline = app.state.pipeline
    fsm: FuelingFSM = app.state.fsm

    if not pipeline.open_source():
        logger.error("Could not open video source in worker loop.")
        return

    logger.info("Video processing worker loop started.")
    fps = settings.VIDEO_FPS
    frame_interval = 1.0 / fps
    last_alarm_logged = 0.0

    while app.state.is_running:
        start_time = time.time()

        if pipeline.paused:
            await asyncio.sleep(0.05)
            continue

        ret, frame, sim_t = pipeline.read_frame()
        if not ret or frame is None:
            await asyncio.sleep(0.01)
            continue

        now = time.time()
        # Process vision frame
        processed_frame, telemetry, safety_status = pipeline.process_single_frame(frame, timestamp=now)

        # FSM State Transitions driven by Vision telemetry
        plate_str = telemetry.get("plate_detected")
        nozzle_in_tank = telemetry.get("nozzle_in_tank", False)
        is_alarm = safety_status.is_alarm

        # Handle Alarm
        if is_alarm:
            if fsm.state != FuelingState.ALARM_LOCKDOWN:
                fsm.trigger_alarm(safety_status.alarm_type or "CRITICAL_HOSE_TEAR_RISK")
                # Record to DB if new alarm
                if now - last_alarm_logged > 3.0:
                    last_alarm_logged = now
                    try:
                        async with AsyncSessionLocal() as db:
                            inc = IncidentLog(
                                incident_type=safety_status.alarm_type or "CRITICAL_HOSE_TEAR_RISK",
                                severity="CRITICAL",
                                description=safety_status.message,
                                displacement_px=safety_status.displacement_px,
                                snapshot_path=safety_status.snapshot_filename,
                            )
                            db.add(inc)
                            await db.commit()
                    except Exception as e:
                        logger.error(f"Error logging incident to DB: {e}")
        else:
            # Normal Flow State Progression
            if fsm.state == FuelingState.IDLE:
                if plate_str:
                    await fsm.identify_plate(plate_str)
            elif fsm.state == FuelingState.PLATE_IDENTIFIED:
                if nozzle_in_tank:
                    fsm.transition_to(FuelingState.NOZZLE_INSERTED)
                    await asyncio.sleep(0.1)
                    fsm.transition_to(FuelingState.FUELING)
            elif fsm.state == FuelingState.FUELING:
                if not nozzle_in_tank:
                    fsm.transition_to(FuelingState.NOZZLE_RETURNED)
                    await fsm.complete_session()
                else:
                    # Increment fuel dispensed (~0.25 L per frame at 30 FPS = ~7.5 L/s demo flow rate)
                    fsm.update_fuel_flow(delta_liters=0.12)
            elif fsm.state == FuelingState.SESSION_COMPLETE:
                # If car departs (no plate or track empty for > 2 sec), return to IDLE
                if time.time() - fsm.state_entry_time > 3.5:
                    fsm.reset_alarm()

        # Broadcast telemetry packet over WebSockets
        packet = {
            "type": "TELEMETRY_UPDATE",
            "fsm": fsm.get_state_payload(),
            "telemetry": telemetry,
        }
        await ws_manager.broadcast_json(packet)

        # Rate control
        elapsed = time.time() - start_time
        sleep_dur = max(0.001, frame_interval - elapsed)
        await asyncio.sleep(sleep_dur)

    logger.info("Video processing worker stopped.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SmartVision AZS Application...")
    await init_db()

    # Generate synthetic video if not exists
    test_video_path = Path(settings.TEST_VIDEO_PATH)
    if not test_video_path.exists():
        logger.info("Generating synthetic scenario test video on first run...")
        generate_synthetic_video()

    # Initialize subsystems
    app.state.pipeline = VisionPipeline(video_source=str(test_video_path))
    app.state.fsm = FuelingFSM()
    app.state.is_running = True

    # Launch background worker
    worker_task = asyncio.create_task(video_pipeline_worker(app))

    yield

    # Shutdown
    logger.info("Shutting down SmartVision AZS Application...")
    app.state.is_running = False
    worker_task.cancel()
    if app.state.pipeline and app.state.pipeline.cap:
        app.state.pipeline.cap.release()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files & APIs
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    """Serve operator dashboard."""
    index_file = static_dir / "index.html"
    return FileResponse(str(index_file))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )

"""
Configuration settings for SmartVision AZS.
Belorusneft Computer Vision & Telemetry System.
"""
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(exist_ok=True, parents=True)


class Settings(BaseSettings):
    # App General
    APP_NAME: str = "SmartVision AZS - Белоруснефть"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'smartvision.db'}"

    # Video & Inference
    TEST_VIDEO_PATH: str = str(DATA_DIR / "test_scenarios.mp4")
    VIDEO_FPS: int = 30
    FRAME_WIDTH: int = 1280
    FRAME_HEIGHT: int = 720
    CONF_THRESHOLD: float = 0.45
    IOU_THRESHOLD: float = 0.45

    # Safety Hose Tear Detection Parameters
    DISPLACEMENT_THRESHOLD_PX: float = 15.0  # ΔD > 15px
    DISPLACEMENT_INTERVAL_MS: float = 300.0  # Time window: 300ms
    PUMP_ZONE: tuple[int, int, int, int] = (850, 180, 1200, 680)  # (x1, y1, x2, y2)
    FUEL_CAP_ZONE_OFFSET: tuple[int, int, int, int] = (150, 100, 320, 260)  # relative to car bbox

    # Fuel Pricing (BYN/Liter)
    FUEL_PRICES: dict[str, float] = {
        "АИ-92": 2.36,
        "АИ-95": 2.46,
        "АИ-98": 2.68,
        "ДТ (Дизель)": 2.46,
        "Газ (ПБА)": 1.28,
        "Электро (кВт·ч)": 0.45,
    }

    # ROI Default Parameters (Republic of Belarus Network)
    DEFAULT_STATION_COUNT: int = 570
    DEFAULT_DAILY_TRAFFIC: int = 750
    DEFAULT_HOSE_INCIDENTS_YEAR: int = 160
    DEFAULT_HOSE_DAMAGE_COST: float = 1200.0  # BYN per tear (coupling, hose, pump downtime)
    DEFAULT_RETAIL_GROWTH_PCT: float = 4.0   # +4.0% sales boost from queue elimination
    DEFAULT_RETAIL_AVERAGE_CHECK: float = 12.50  # BYN
    DEFAULT_RETAIL_MARGIN_PCT: float = 28.0     # 28% retail margin
    DEFAULT_SYSTEM_CAPEX: float = 380000.0      # BYN network roll-out Capex


settings = Settings()

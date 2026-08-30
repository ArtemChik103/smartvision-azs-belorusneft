"""API endpoints and WebSocket handlers for SmartVision AZS."""
from .routes import router as api_router
from .ws_handler import router as ws_router

__all__ = ["api_router", "ws_router"]

"""
Asynchronous Event Bus & WebSocket Connection Manager for SmartVision AZS.
"""
import asyncio
import json
import logging
from typing import Dict, Set, Callable, Any
from fastapi import WebSocket

logger = logging.getLogger("smartvision.events")


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, Set[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)

    async def publish(self, event_type: str, data: Any = None) -> None:
        if event_type in self._subscribers:
            tasks = []
            for cb in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(cb):
                        tasks.append(asyncio.create_task(cb(data)))
                    else:
                        cb(data)
                except Exception as e:
                    logger.error(f"Error invoking subscriber for event '{event_type}': {e}")
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_json(self, message: Dict[str, Any]) -> None:
        if not self.active_connections:
            return

        text = json.dumps(message, ensure_ascii=False)
        async with self._lock:
            connections = list(self.active_connections)

        if not connections:
            return

        async def _safe_send(ws: WebSocket):
            try:
                await asyncio.wait_for(ws.send_text(text), timeout=0.5)
                return None
            except Exception:
                return ws

        results = await asyncio.gather(*(_safe_send(ws) for ws in connections), return_exceptions=False)
        disconnected = [r for r in results if isinstance(r, WebSocket)]

        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    self.active_connections.discard(ws)


event_bus = EventBus()
ws_manager = ConnectionManager()

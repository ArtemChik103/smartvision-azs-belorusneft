"""
WebSocket handler for real-time video telemetry, bounding boxes, and bi-directional control.
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.events import ws_manager

logger = logging.getLogger("smartvision.ws")
router = APIRouter(tags=["WebSocket Telemetry"])


@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Handle incoming control commands from operator UI
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                cmd = msg.get("command")
                app = websocket.app
                pipeline = getattr(app.state, "pipeline", None)
                fsm = getattr(app.state, "fsm", None)

                if cmd == "EMERGENCY_STOP":
                    if pipeline:
                        pipeline.safety_engine.set_manual_e_stop(True)
                    if fsm:
                        fsm.trigger_alarm("MANUAL_EMERGENCY_STOP")
                elif cmd == "RESET_ALARM":
                    if pipeline:
                        pipeline.safety_engine.reset_alarm()
                    if fsm:
                        fsm.reset_alarm()
                elif cmd == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
            except Exception as e:
                logger.error(f"Error parsing incoming WS message: {e}")

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        await ws_manager.disconnect(websocket)

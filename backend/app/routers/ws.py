from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from structlog import get_logger

from app.services.auth import get_current_user
from app.services.ws_manager import ws_manager

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/api/v1/ws/jobs/{job_id}")
async def job_websocket(websocket: WebSocket, job_id: str):
    await ws_manager.connect(job_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(job_id, websocket)
    except Exception as e:
        logger.warning("ws_error", job_id=job_id, error=str(e))
        ws_manager.disconnect(job_id, websocket)

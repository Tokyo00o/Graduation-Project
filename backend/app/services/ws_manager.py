import asyncio
from typing import Any, Dict, Set

from fastapi import WebSocket
from structlog import get_logger

logger = get_logger(__name__)


class WSManager:
    """Manages WebSocket connections per job ID with cross-thread broadcasting."""

    _main_loop: asyncio.AbstractEventLoop = None

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}

    @classmethod
    def set_main_loop(cls, loop: asyncio.AbstractEventLoop) -> None:
        cls._main_loop = loop

    @classmethod
    def get_main_loop(cls) -> asyncio.AbstractEventLoop:
        return cls._main_loop

    async def connect(self, job_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(job_id, set()).add(ws)
        count = len(self._connections.get(job_id, set()))
        logger.info("ws_connected", job_id=job_id, connections=count)

    def disconnect(self, job_id: str, ws: WebSocket) -> None:
        self._connections.get(job_id, set()).discard(ws)
        count = len(self._connections.get(job_id, set()))
        logger.info("ws_disconnected", job_id=job_id, connections=count)

    async def broadcast(self, job_id: str, message: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections.get(job_id, set()):
            try:
                await ws.send_json(message)
            except Exception as exc:
                logger.warning("ws_send_error", job_id=job_id, error=str(exc))
                dead.append(ws)
        for ws in dead:
            self._connections.get(job_id, set()).discard(ws)

    def broadcast_sync(self, job_id: str, message: dict) -> None:
        loop = self._main_loop
        if loop is None or loop.is_closed():
            logger.warning("ws_broadcast_no_loop", job_id=job_id)
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(job_id, message), loop)


ws_manager = WSManager()

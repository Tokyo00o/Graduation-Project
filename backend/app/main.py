import asyncio
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.config import settings
from app.database import Base, engine
from app.routers import alerts, auth, benchmarks, jobs, judgment, keys, models_targets, projects, reports, schedules, seed_library, seeds, ws
from app.services.ws_manager import ws_manager
from app.services.scheduler import scheduler_service

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)

# -- Logging --
from app.services.logging import setup_logging as _setup_logging
_log = _setup_logging(
    service_name=settings.app_name,
    log_level=settings.log_level,
    json_format=settings.log_json,
)

# -- Prometheus middleware --
if settings.metrics_enabled:
    from app.services.metrics import PrometheusMiddleware
    app.add_middleware(PrometheusMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Request logging middleware (ASGI, avoids BaseHTTPMiddleware stacking issues) --
@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/metrics", "/favicon.ico"):
        return await call_next(request)
    start = time.monotonic()
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as exc:
        status = 500
        _log.error("request_failed", path=request.url.path, method=request.method, error=str(exc))
        raise
    finally:
        duration = time.monotonic() - start
        _log.info("request", method=request.method, path=request.url.path, status=status, duration_ms=round(duration * 1000, 1))
    return response

app.include_router(projects.router)
app.include_router(seeds.router)
app.include_router(jobs.router)
app.include_router(models_targets.router)
app.include_router(judgment.router)
app.include_router(keys.router)
app.include_router(reports.router)
app.include_router(seed_library.router)
app.include_router(benchmarks.router)
app.include_router(auth.router)
app.include_router(ws.router)
app.include_router(schedules.router)
app.include_router(alerts.router)

# -- OpenTelemetry tracing --
if settings.tracing_enabled:
    from app.services.tracing import setup_tracing as _setup_tracing
    _setup_tracing(
        app,
        service_name=settings.app_name,
        otlp_endpoint=settings.tracing_otlp_endpoint or None,
        enable_console=settings.tracing_console,
    )
    _log.info("tracing_enabled", otlp_endpoint=settings.tracing_otlp_endpoint or "console")

# Store event loop reference for cross-thread WebSocket broadcasting
try:
    ws_manager.set_main_loop(asyncio.get_running_loop())
except RuntimeError:
    pass  # no running event loop (e.g. during tests)

# Start background scheduler
if settings.scheduler_enabled:
    scheduler_service.start()
    _log.info("scheduler_started", interval_seconds=settings.scheduler_check_interval)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.1.0",
        "uptime": time.monotonic(),
    }


@app.get("/metrics")
def metrics():
    if not settings.metrics_enabled:
        return Response(status_code=404, content='{"error":"metrics disabled"}', media_type="application/json")
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

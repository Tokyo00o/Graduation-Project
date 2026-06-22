import time

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST


http_requests_total = Counter(
    "fuzzguard_http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "fuzzguard_http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "path", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

active_ws_connections = Gauge(
    "fuzzguard_active_ws_connections",
    "Active WebSocket connections",
)

jobs_total = Counter(
    "fuzzguard_jobs_total",
    "Total jobs created",
    labelnames=["status", "strategy"],
)

active_jobs = Gauge(
    "fuzzguard_active_jobs",
    "Currently running jobs",
)

iterations_total = Counter(
    "fuzzguard_iterations_total",
    "Total fuzzing iterations executed",
    labelnames=["strategy"],
)

jailbreaks_total = Counter(
    "fuzzguard_jailbreaks_total",
    "Total jailbreak detections",
    labelnames=["strategy", "classification"],
)

asr_gauge = Gauge(
    "fuzzguard_asr",
    "Current attack success rate across jobs",
    labelnames=["job_id"],
)

seeds_total = Counter(
    "fuzzguard_seeds_total",
    "Total seeds created",
    labelnames=["source"],
)

judgments_total = Counter(
    "fuzzguard_judgments_total",
    "Total judgments performed",
    labelnames=["judge_model", "classification"],
)

llm_requests_total = Counter(
    "fuzzguard_llm_requests_total",
    "Total LLM provider requests",
    labelnames=["provider", "status"],
)

schedules_total = Counter(
    "fuzzguard_schedules_total",
    "Total scheduled job triggers",
)

alerts_total = Counter(
    "fuzzguard_alerts_total",
    "Total alerts triggered",
    labelnames=["channel"],
)


class PrometheusMiddleware:
    """ASGI middleware for Prometheus HTTP metrics (avoids BaseHTTPMiddleware stacking issues)."""

    def __init__(self, app, exclude_paths: set = None):
        self.app = app
        self.exclude_paths = exclude_paths or {"/metrics", "/health"}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self.exclude_paths:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        start = time.monotonic()
        status_code = [500]

        async def _send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, _send)
        except Exception:
            raise
        finally:
            duration = time.monotonic() - start
            http_requests_total.labels(method=method, path=path, status=status_code[0]).inc()
            http_request_duration_seconds.labels(method=method, path=path, status=status_code[0]).observe(duration)

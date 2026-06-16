import logging
import sys

import structlog


def setup_logging(service_name: str = "fuzzguard", log_level: str = "INFO", json_format: bool = True):
    level = getattr(logging, log_level.upper(), logging.INFO)

    structlog_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        structlog_processors.append(structlog.processors.JSONRenderer())
    else:
        structlog_processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=structlog_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    for logr in ("uvicorn", "uvicorn.access", "uvicorn.error", "sqlalchemy.engine"):
        logging.getLogger(logr).handlers.clear()
        logging.getLogger(logr).propagate = False

    logging.getLogger("uvicorn").handlers.append(logging.StreamHandler(sys.stdout))
    logging.getLogger("uvicorn").setLevel(level)

    return structlog.get_logger(service_name)


def get_logger(name: str = None):
    return structlog.get_logger(name or __name__)

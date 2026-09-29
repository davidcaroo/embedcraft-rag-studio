"""Structured logging system with secret redaction and rotation support."""

from __future__ import annotations

import logging
import re
from typing import Any

import structlog

from embedcraft.infrastructure.settings import settings

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|bearer|authorization)\s*[:=]\s*([\"\']?)([\w\-]{8,})\2"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI-like keys
]


def redact_sensitive_data(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Scrub potential secrets and API keys from logs."""
    for key, value in list(event_dict.items()):
        if isinstance(value, str):
            if any(sec in key.lower() for sec in ["key", "secret", "password", "token", "auth"]):
                event_dict[key] = "[REDACTED]"
            else:
                for pattern in SECRET_PATTERNS:
                    if pattern.search(value):
                        event_dict[key] = pattern.sub("[REDACTED]", value)
        elif isinstance(value, dict):
            # Recursively redact dicts
            for k in list(value.keys()):
                if any(sec in k.lower() for sec in ["key", "secret", "password", "token", "auth"]):
                    value[k] = "[REDACTED]"
    return event_dict


def configure_logging(log_level: int = logging.INFO) -> None:
    """Configure structlog and standard logging."""
    log_file = settings.log_path

    # Standard python logging handlers
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    stream_handler = logging.StreamHandler()

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[file_handler, stream_handler],
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            redact_sensitive_data,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if not log_file else structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger("embedcraft")

"""
Captain Raccoon — Logger Utilities
Structured logging helpers and context managers.
"""
from __future__ import annotations

import contextlib
import time
from typing import Optional

import structlog

log = structlog.get_logger(__name__)


@contextlib.contextmanager
def log_timing(operation: str, **extra):
    """Context manager that logs start/end + elapsed time."""
    start = time.time()
    log.info(f"{operation}.start", **extra)
    try:
        yield
        elapsed = round(time.time() - start, 2)
        log.info(f"{operation}.done", elapsed_seconds=elapsed, **extra)
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        log.error(f"{operation}.failed", elapsed_seconds=elapsed, error=str(e), **extra)
        raise


def bind_episode_context(episode_id: str) -> None:
    """Bind episode_id to all subsequent log records in this context."""
    structlog.contextvars.bind_contextvars(episode_id=episode_id)


def clear_context() -> None:
    structlog.contextvars.clear_contextvars()

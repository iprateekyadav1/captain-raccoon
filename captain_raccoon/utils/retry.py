"""
Captain Raccoon — Retry Utilities
Exponential backoff with jitter for all external API calls.
"""
from __future__ import annotations

import functools
import random
import time
from typing import Any, Callable, Optional, Type, Tuple

import structlog

log = structlog.get_logger(__name__)


def with_retry(
    max_attempts: int = 3,
    wait_fixed: float = 2.0,
    wait_multiplier: float = 2.0,
    wait_max: float = 120.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    dont_retry_on: Optional[Tuple[Type[Exception], ...]] = None,
):
    """
    Decorator for automatic retry with exponential backoff.

    Usage:
        @with_retry(max_attempts=3)
        def my_api_call():
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            last_exc: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)

                except Exception as exc:
                    # Check if we should NOT retry this exception type
                    if dont_retry_on and isinstance(exc, dont_retry_on):
                        raise

                    # Check if we should retry this exception type
                    if not isinstance(exc, retry_on):
                        raise

                    last_exc = exc

                    if attempt == max_attempts:
                        log.error(
                            "retry.exhausted",
                            fn=fn.__name__,
                            attempts=max_attempts,
                            error=str(exc),
                        )
                        break

                    # Calculate wait time with exponential backoff
                    wait = min(wait_fixed * (wait_multiplier ** (attempt - 1)), wait_max)
                    if jitter:
                        wait = wait * (0.5 + random.random() * 0.5)

                    log.warning(
                        "retry.waiting",
                        fn=fn.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        wait_seconds=round(wait, 1),
                        error=str(exc),
                    )
                    time.sleep(wait)

            raise last_exc

        return wrapper
    return decorator


def retry_on_rate_limit(fn: Callable) -> Callable:
    """Specialized retry for API rate limit (429) responses."""
    import httpx

    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> Any:
        for attempt in range(1, 6):
            try:
                return fn(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = float(e.response.headers.get("Retry-After", 60))
                    log.warning(
                        "retry.rate_limited",
                        fn=fn.__name__,
                        attempt=attempt,
                        retry_after=retry_after,
                    )
                    time.sleep(retry_after)
                    continue
                raise
        raise RuntimeError(f"Rate limit exceeded after 5 attempts: {fn.__name__}")

    return wrapper

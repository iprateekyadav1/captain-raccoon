"""
Captain Raccoon — Monitoring Setup
Initializes Sentry, Datadog, and New Relic.
Provides unified track_metric() and capture_exception() helpers.
"""
from __future__ import annotations

import os
import functools
import time
from typing import Any, Callable, Optional

import structlog

log = structlog.get_logger(__name__)

_sentry_initialized = False
_datadog_initialized = False
_newrelic_initialized = False


# =============================================================================
# INITIALIZATION
# =============================================================================
def init_monitoring() -> None:
    """Call once at application startup."""
    _init_sentry()
    _init_datadog()
    _init_newrelic()
    _configure_structlog()
    log.info("monitoring.initialized")


def _init_sentry() -> None:
    global _sentry_initialized
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        log.warning("monitoring.sentry_disabled", reason="no SENTRY_DSN")
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("ENVIRONMENT", "development"),
            release=f"captain-raccoon@{os.getenv('APP_VERSION', '1.0.0')}",
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")),
            profiles_sample_rate=0.1,
            integrations=[LoggingIntegration(level=None, event_level="ERROR")],
            send_default_pii=False,
        )
        _sentry_initialized = True
        log.info("monitoring.sentry_ready")
    except Exception as e:
        log.warning("monitoring.sentry_failed", error=str(e))


def _init_datadog() -> None:
    global _datadog_initialized
    api_key = os.getenv("DATADOG_API_KEY", "")
    if not api_key:
        log.warning("monitoring.datadog_disabled", reason="no DATADOG_API_KEY")
        return
    try:
        from datadog import initialize, statsd

        initialize(
            api_key=api_key,
            app_key=os.getenv("DATADOG_APP_KEY", ""),
            statsd_host=os.getenv("DD_AGENT_HOST", "localhost"),
            statsd_port=int(os.getenv("DD_DOGSTATSD_PORT", "8125")),
        )
        _datadog_initialized = True
        log.info("monitoring.datadog_ready")
    except Exception as e:
        log.warning("monitoring.datadog_failed", error=str(e))


def _init_newrelic() -> None:
    global _newrelic_initialized
    license_key = os.getenv("NEW_RELIC_LICENSE_KEY", "")
    if not license_key:
        log.warning("monitoring.newrelic_disabled", reason="no NEW_RELIC_LICENSE_KEY")
        return
    try:
        import newrelic.agent

        newrelic.agent.initialize()
        _newrelic_initialized = True
        log.info("monitoring.newrelic_ready")
    except Exception as e:
        log.warning("monitoring.newrelic_failed", error=str(e))


def _configure_structlog() -> None:
    """Configure structured logging with JSON output in production."""
    import logging
    import structlog

    is_prod = os.getenv("ENVIRONMENT", "development") == "production"
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_prod:
        # JSON output for log aggregation (Datadog / New Relic)
        structlog.configure(
            processors=shared_processors + [structlog.processors.JSONRenderer()],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level, logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Pretty console output for development
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True)
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level, logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


# =============================================================================
# UNIFIED HELPERS
# =============================================================================
def track_metric(
    metric_name: str,
    value: float = 1,
    tags: Optional[dict] = None,
    metric_type: str = "gauge",
) -> None:
    """
    Send a metric to Datadog (if configured) + log it.
    metric_type: gauge | count | histogram | timing
    """
    tag_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
    tag_list += [
        f"env:{os.getenv('ENVIRONMENT', 'development')}",
        "service:captain-raccoon",
    ]

    if _datadog_initialized:
        try:
            from datadog import statsd

            fn_map = {
                "gauge":     statsd.gauge,
                "count":     statsd.increment,
                "histogram": statsd.histogram,
                "timing":    statsd.timing,
            }
            fn = fn_map.get(metric_type, statsd.gauge)
            fn(f"captain_raccoon.{metric_name}", value, tags=tag_list)
        except Exception as e:
            log.debug("monitoring.metric_failed", metric=metric_name, error=str(e))

    log.debug("metric", name=metric_name, value=value, tags=tags)


def capture_exception(exc: Exception, context: Optional[dict] = None) -> None:
    """Send exception to Sentry (if configured) + log it."""
    if _sentry_initialized:
        try:
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                if context:
                    for k, v in context.items():
                        scope.set_extra(k, v)
                sentry_sdk.capture_exception(exc)
        except Exception:
            pass

    log.error("exception_captured", exc_type=type(exc).__name__, error=str(exc))


# =============================================================================
# TIMING DECORATOR
# =============================================================================
def timed(metric_name: Optional[str] = None, tags: Optional[dict] = None):
    """Decorator that tracks function execution time."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                elapsed_ms = int((time.time() - start) * 1000)
                name = metric_name or f"fn.{fn.__name__}"
                track_metric(name, elapsed_ms, tags=tags, metric_type="timing")
                return result
            except Exception as e:
                capture_exception(e)
                raise
        return wrapper
    return decorator

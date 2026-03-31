"""
Captain Raccoon — Scheduler
Runs the pipeline on a cron schedule.
Designed to run as a Heroku worker or standalone process.
"""
from __future__ import annotations

import signal
import sys
import time
from datetime import datetime, timezone

import schedule
import structlog

from captain_raccoon.config.settings import get_pipeline_config
from captain_raccoon.monitoring.setup import init_monitoring, track_metric
from captain_raccoon.orchestrator.pipeline import CaptainRaccoonPipeline

log = structlog.get_logger(__name__)
_pipeline: CaptainRaccoonPipeline | None = None


def _get_pipeline() -> CaptainRaccoonPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = CaptainRaccoonPipeline()
    return _pipeline


def run_generation_job() -> None:
    """Scheduled job: generate 1 episode."""
    log.info("scheduler.job_triggered", job="generate_episode")
    track_metric("scheduler.job_triggered", 1, tags={"job": "generate"})
    try:
        _get_pipeline().run_single(publish=False)  # Generate only — publish separately
        log.info("scheduler.job_done", job="generate_episode")
    except Exception as e:
        log.error("scheduler.job_failed", job="generate_episode", error=str(e))
        track_metric("scheduler.job_failed", 1, tags={"job": "generate"})


def run_publish_job() -> None:
    """Scheduled job: publish all assembled-but-unpublished episodes."""
    from captain_raccoon.database.models import EpisodeStatus
    from captain_raccoon.database.repository import EpisodeRepository

    log.info("scheduler.job_triggered", job="publish_episodes")
    repo = EpisodeRepository()
    assembled = repo.get_by_status(EpisodeStatus.ASSEMBLED)

    if not assembled:
        log.info("scheduler.no_episodes_to_publish")
        return

    pipeline = _get_pipeline()
    for ep in assembled:
        try:
            pipeline._run_publish_stage(ep)
        except Exception as e:
            log.error("scheduler.publish_failed", episode_id=ep.episode_id, error=str(e))


def run_full_pipeline_job() -> None:
    """Scheduled job: generate + publish in one shot."""
    log.info("scheduler.job_triggered", job="full_pipeline")
    try:
        _get_pipeline().run_single(publish=True)
    except Exception as e:
        log.error("scheduler.full_pipeline_failed", error=str(e))


def start(mode: str = "full") -> None:
    """
    Start the scheduler.
    mode: full | generate_only | publish_only
    """
    init_monitoring()
    config = get_pipeline_config()

    gen_time  = config.get("scheduling", "generation_time_utc", default="06:00")
    pub_time  = config.get("scheduling", "publish_time_utc", default="14:00")
    gen_days  = config.get("scheduling", "generation_days", default=["monday", "wednesday", "friday"])
    pub_days  = config.get("scheduling", "publish_days", default=["tuesday", "thursday", "saturday"])

    log.info("scheduler.starting", mode=mode, gen_time=gen_time, pub_time=pub_time)

    if mode in ("full",):
        for day in gen_days:
            getattr(schedule.every(), day).at(gen_time).do(run_generation_job)
        for day in pub_days:
            getattr(schedule.every(), day).at(pub_time).do(run_publish_job)
    elif mode == "generate_only":
        for day in gen_days:
            getattr(schedule.every(), day).at(gen_time).do(run_generation_job)
    elif mode == "publish_only":
        for day in pub_days:
            getattr(schedule.every(), day).at(pub_time).do(run_publish_job)
    elif mode == "continuous":
        # Dev mode: run every hour
        schedule.every().hour.do(run_full_pipeline_job)

    # Graceful shutdown
    def _shutdown(signum, frame):
        log.info("scheduler.shutting_down")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    log.info("scheduler.running", jobs=len(schedule.jobs))
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    start(mode=mode)

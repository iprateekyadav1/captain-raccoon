"""
Captain Raccoon — Instagram Publisher
Posts Reels to Instagram using the Instagram Graph API.
Supports two-phase upload (container create → publish).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx
import structlog

from captain_raccoon.config.settings import get_settings, get_pipeline_config
from captain_raccoon.engines.assembly_engine import AssembledEpisode
from captain_raccoon.engines.story_engine import EpisodeScript
from captain_raccoon.monitoring.setup import track_metric, capture_exception
from captain_raccoon.utils.retry import with_retry
from captain_raccoon.utils.storage import StorageManager

log = structlog.get_logger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


# =============================================================================
# DATA MODELS
# =============================================================================
@dataclass
class InstagramPostResult:
    media_id: str
    post_url: str
    caption_used: str
    upload_time_seconds: float


# =============================================================================
# INSTAGRAM PUBLISHER
# =============================================================================
class InstagramPublisher:
    """
    Posts Captain Raccoon Reels to Instagram via Graph API.

    Instagram Reels upload flow:
    1. Upload video to cloud storage (Azure Blob / DO Spaces) → get public URL
    2. Create media container via Graph API
    3. Poll container status until FINISHED
    4. Publish container
    """

    POLL_INTERVAL_SEC = 10
    POLL_MAX_ATTEMPTS = 60      # 10 minutes max

    def __init__(self):
        self._settings = get_settings()
        self._config = get_pipeline_config()
        self._storage = StorageManager()

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────
    def publish(
        self,
        episode: AssembledEpisode,
        script: EpisodeScript,
    ) -> Optional[InstagramPostResult]:
        """
        Upload and publish episode as an Instagram Reel.
        """
        if not self._config.get("publishing", "instagram", "enabled"):
            log.info("instagram_publisher.disabled")
            return None

        access_token = self._settings.instagram_access_token
        account_id = self._settings.instagram_account_id
        if not access_token or not account_id:
            log.error("instagram_publisher.missing_credentials")
            return None

        start = time.time()

        # Step 1: Upload video to cloud → get public URL
        log.info("instagram_publisher.uploading_to_storage", episode_id=episode.episode_id)
        video_url = self._storage.upload_for_instagram(
            local_path=episode.final_path,
            object_key=f"instagram/{episode.episode_id}.mp4",
        )

        # Step 2: Build caption
        caption = self._build_caption(script)

        # Step 3: Create media container
        container_id = self._create_reel_container(
            account_id=account_id,
            access_token=access_token,
            video_url=video_url,
            caption=caption,
        )
        log.info("instagram_publisher.container_created", container_id=container_id)

        # Step 4: Poll until container is ready
        self._wait_for_container(
            account_id=account_id,
            container_id=container_id,
            access_token=access_token,
        )

        # Step 5: Publish
        media_id = self._publish_container(
            account_id=account_id,
            container_id=container_id,
            access_token=access_token,
        )

        elapsed = round(time.time() - start, 1)
        post_url = f"https://www.instagram.com/p/{media_id}/"

        track_metric("instagram_publisher.publish_success", 1)
        track_metric("instagram_publisher.publish_seconds", elapsed)

        log.info(
            "instagram_publisher.done",
            media_id=media_id,
            url=post_url,
            seconds=elapsed,
        )

        return InstagramPostResult(
            media_id=media_id,
            post_url=post_url,
            caption_used=caption[:100] + "...",
            upload_time_seconds=elapsed,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # GRAPH API CALLS
    # ─────────────────────────────────────────────────────────────────────────
    @with_retry(max_attempts=3)
    def _create_reel_container(
        self,
        account_id: str,
        access_token: str,
        video_url: str,
        caption: str,
    ) -> str:
        """Step 1: Create Instagram Reels media container."""
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{GRAPH_API_BASE}/{account_id}/media",
                params={
                    "access_token": access_token,
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": caption,
                    "share_to_feed": str(
                        self._config.get("publishing", "instagram", "share_to_feed", default=True)
                    ).lower(),
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(f"Instagram API error: {data['error']}")
            return data["id"]

    def _wait_for_container(
        self, account_id: str, container_id: str, access_token: str
    ) -> None:
        """Poll until the media container finishes processing."""
        for attempt in range(self.POLL_MAX_ATTEMPTS):
            status = self._get_container_status(container_id, access_token)
            log.debug("instagram_publisher.container_status", status=status, attempt=attempt)

            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(f"Instagram container failed: {container_id}")
            if status in ("EXPIRED", "DELETED"):
                raise RuntimeError(f"Instagram container {status}: {container_id}")

            time.sleep(self.POLL_INTERVAL_SEC)

        raise TimeoutError(f"Container {container_id} timed out after {self.POLL_MAX_ATTEMPTS * self.POLL_INTERVAL_SEC}s")

    def _get_container_status(self, container_id: str, access_token: str) -> str:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                f"{GRAPH_API_BASE}/{container_id}",
                params={
                    "fields": "status_code",
                    "access_token": access_token,
                },
            )
            resp.raise_for_status()
            return resp.json().get("status_code", "UNKNOWN")

    @with_retry(max_attempts=3)
    def _publish_container(
        self, account_id: str, container_id: str, access_token: str
    ) -> str:
        """Publish the ready container."""
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{GRAPH_API_BASE}/{account_id}/media_publish",
                params={
                    "access_token": access_token,
                    "creation_id": container_id,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(f"Instagram publish error: {data['error']}")
            return data["id"]

    # ─────────────────────────────────────────────────────────────────────────
    # CAPTION BUILDER
    # ─────────────────────────────────────────────────────────────────────────
    def _build_caption(self, script: EpisodeScript) -> str:
        """Build Instagram caption from script."""
        default_hashtags = self._config.get(
            "publishing", "instagram", "default_hashtags", default=[]
        )
        script_hashtags = [f"#{t.lstrip('#')}" for t in script.hashtags[:5]]
        extra_hashtags = [h for h in default_hashtags if h not in script_hashtags][:5]

        all_hashtags = script_hashtags + extra_hashtags
        hashtag_str = " ".join(all_hashtags)

        caption = f"{script.instagram_caption}\n\n{hashtag_str}"
        return caption[:2200]   # Instagram caption limit

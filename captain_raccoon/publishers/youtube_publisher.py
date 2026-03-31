"""
Captain Raccoon — YouTube Publisher
Uploads finished episodes to YouTube using the Data API v3.
Handles OAuth2, Shorts detection, scheduling, and retry.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from captain_raccoon.config.settings import get_settings, get_pipeline_config
from captain_raccoon.engines.assembly_engine import AssembledEpisode
from captain_raccoon.engines.story_engine import EpisodeScript
from captain_raccoon.monitoring.setup import track_metric, capture_exception
from captain_raccoon.utils.retry import with_retry

log = structlog.get_logger(__name__)

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


# =============================================================================
# DATA MODELS
# =============================================================================
@dataclass
class YouTubeUploadResult:
    video_id: str
    video_url: str
    title: str
    privacy_status: str
    upload_time_seconds: float


# =============================================================================
# YOUTUBE PUBLISHER
# =============================================================================
class YouTubePublisher:
    """
    Uploads Captain Raccoon episodes to YouTube.
    - Auto-detects Shorts (≤ 60s in 9:16) and adds #Shorts tag
    - Generates SEO title + description from episode script
    - Sets thumbnail automatically
    - Supports scheduled publishing
    """

    UPLOAD_CHUNKSIZE = 1024 * 1024 * 5     # 5 MB chunks

    def __init__(self):
        self._settings = get_settings()
        self._config = get_pipeline_config()
        self._youtube = None                # Lazy-init

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────
    def publish(
        self,
        episode: AssembledEpisode,
        script: EpisodeScript,
        schedule_time: Optional[str] = None,    # ISO 8601 e.g. "2025-06-01T14:00:00Z"
    ) -> YouTubeUploadResult:
        """
        Upload episode to YouTube.

        Args:
            episode: Assembled video + thumbnail
            script:  Episode script (for title / description / tags)
            schedule_time: If set, video is scheduled (unlisted until then)
        """
        if not self._config.get("publishing", "youtube", "enabled"):
            log.info("youtube_publisher.disabled")
            return None

        youtube = self._get_youtube_client()
        start = time.time()

        title = self._build_title(script, episode)
        description = self._build_description(script)
        tags = self._build_tags(script, episode)
        privacy = "private" if schedule_time else self._config.get(
            "publishing", "youtube", "privacy_status", default="public"
        )

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": self._config.get("publishing", "youtube", "category_id", default="22"),
                "defaultLanguage": "en",
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
                "notifySubscribers": True,
            },
        }

        if schedule_time:
            body["status"]["publishAt"] = schedule_time
            body["status"]["privacyStatus"] = "private"

        media = MediaFileUpload(
            str(episode.final_path),
            mimetype="video/mp4",
            chunksize=self.UPLOAD_CHUNKSIZE,
            resumable=True,
        )

        log.info("youtube_publisher.uploading", title=title, size_mb=round(episode.file_size_bytes / 1_048_576, 1))

        video_id = self._upload_with_retry(youtube, body, media)
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Set thumbnail
        if episode.thumbnail_path.exists():
            self._set_thumbnail(youtube, video_id, episode.thumbnail_path)

        elapsed = round(time.time() - start, 1)
        track_metric("youtube_publisher.upload_success", 1)
        track_metric("youtube_publisher.upload_seconds", elapsed)

        log.info(
            "youtube_publisher.done",
            video_id=video_id,
            url=video_url,
            seconds=elapsed,
        )

        return YouTubeUploadResult(
            video_id=video_id,
            video_url=video_url,
            title=title,
            privacy_status=privacy,
            upload_time_seconds=elapsed,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE
    # ─────────────────────────────────────────────────────────────────────────
    def _get_youtube_client(self):
        """Build authenticated YouTube API client using stored OAuth tokens."""
        if self._youtube:
            return self._youtube

        creds = Credentials(
            token=None,
            refresh_token=self._settings.youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self._settings.youtube_client_id,
            client_secret=self._settings.youtube_client_secret,
            scopes=YOUTUBE_SCOPES,
        )
        # Refresh the token
        creds.refresh(Request())
        self._youtube = build("youtube", "v3", credentials=creds)
        return self._youtube

    @with_retry(max_attempts=3, wait_fixed=10)
    def _upload_with_retry(self, youtube, body: dict, media: MediaFileUpload) -> str:
        """Upload video with resumable upload + exponential backoff."""
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    pct = int(status.progress() * 100)
                    log.debug("youtube_publisher.progress", pct=pct)
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    time.sleep(5)
                    continue
                raise

        return response["id"]

    def _set_thumbnail(self, youtube, video_id: str, thumbnail_path: Path) -> None:
        """Upload custom thumbnail to YouTube."""
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg"),
            ).execute()
            log.debug("youtube_publisher.thumbnail_set", video_id=video_id)
        except Exception as e:
            log.warning("youtube_publisher.thumbnail_failed", error=str(e))
            capture_exception(e)

    def _build_title(self, script: EpisodeScript, episode: AssembledEpisode) -> str:
        """Build SEO-optimized title. Adds #Shorts suffix for short videos."""
        title = script.youtube_title or script.title
        if episode.duration_seconds <= 62:
            if "#Shorts" not in title:
                title = f"{title} #Shorts"
        # YouTube title max 100 chars
        return title[:100]

    def _build_description(self, script: EpisodeScript) -> str:
        """Build YouTube video description."""
        default_tags = self._config.get("publishing", "youtube", "default_tags", default=[])
        hashtags_str = " ".join(f"#{t.lstrip('#')}" for t in default_tags[:5])

        description = f"""{script.youtube_description}

🦝 Follow Captain Raccoon's adventures across The Sprawl.
New episodes every week — stories about kindness, resilience, and finding your place.

{hashtags_str}

---
🎬 Created with AI storytelling + animation pipeline
📖 Story generated with Claude AI
🎨 Visuals powered by FLUX.1 + Wan 2.1
"""
        return description[:5000]  # YouTube description limit

    def _build_tags(self, script: EpisodeScript, episode: AssembledEpisode) -> list[str]:
        """Build tag list combining script tags + default channel tags."""
        default = self._config.get("publishing", "youtube", "default_tags", default=[])
        script_tags = [t.lstrip("#") for t in script.hashtags]
        all_tags = list(dict.fromkeys(default + script_tags))  # dedupe, preserve order
        if episode.duration_seconds <= 62:
            all_tags = ["Shorts"] + all_tags
        return all_tags[:500]  # YouTube tag limit

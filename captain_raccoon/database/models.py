"""
Captain Raccoon — MongoDB Data Models
All episode metadata, generation state, and publish records stored here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================
class EpisodeStatus(str, Enum):
    QUEUED          = "queued"
    GENERATING      = "generating"
    IMAGES_DONE     = "images_done"
    VIDEOS_DONE     = "videos_done"
    AUDIO_DONE      = "audio_done"
    ASSEMBLED       = "assembled"
    PUBLISHED       = "published"
    FAILED          = "failed"


class Provider(str, Enum):
    REPLICATE       = "replicate"
    HUGGINGFACE     = "huggingface"
    LOCAL           = "local"
    AZURE           = "azure"
    GOOGLE          = "google"
    COQUI           = "coqui"


# =============================================================================
# SCENE DOCUMENT
# =============================================================================
class SceneDoc(BaseModel):
    scene_number: int
    narration: str
    visual_description: str
    emotion: str
    setting: str
    action: str
    duration_seconds: float
    image_url: Optional[str] = None
    image_local_path: Optional[str] = None
    image_provider: Optional[str] = None
    image_generation_ms: Optional[int] = None
    video_url: Optional[str] = None
    video_local_path: Optional[str] = None
    video_provider: Optional[str] = None
    video_generation_ms: Optional[int] = None
    audio_local_path: Optional[str] = None
    tts_provider: Optional[str] = None
    tts_duration_seconds: Optional[float] = None


# =============================================================================
# PUBLISH RECORD
# =============================================================================
class YouTubeRecord(BaseModel):
    video_id: str
    video_url: str
    title: str
    privacy_status: str
    published_at: datetime
    upload_duration_seconds: float
    views: int = 0
    likes: int = 0
    comments: int = 0


class InstagramRecord(BaseModel):
    media_id: str
    post_url: str
    published_at: datetime
    upload_duration_seconds: float
    likes: int = 0
    comments: int = 0
    reach: int = 0


# =============================================================================
# EPISODE DOCUMENT  (main MongoDB document)
# =============================================================================
class EpisodeDoc(BaseModel):
    # ── Identity ──────────────────────────────────────────────────────────────
    episode_id: str                     # UUID, e.g. "ep_20250601_abc123"
    title: str
    logline: str
    theme: str
    status: EpisodeStatus = EpisodeStatus.QUEUED
    version: int = 1                    # Increment on retry

    # ── Script ────────────────────────────────────────────────────────────────
    hook: str = ""
    call_to_action: str = ""
    hashtags: list[str] = Field(default_factory=list)
    youtube_title: str = ""
    youtube_description: str = ""
    instagram_caption: str = ""
    total_duration_seconds: float = 0.0
    word_count: int = 0
    scenes: list[SceneDoc] = Field(default_factory=list)

    # ── Asset Paths ───────────────────────────────────────────────────────────
    final_video_path: Optional[str] = None
    final_video_url: Optional[str] = None     # Cloud storage URL
    thumbnail_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    audio_path: Optional[str] = None

    # ── Publish Records ───────────────────────────────────────────────────────
    youtube: Optional[YouTubeRecord] = None
    instagram: Optional[InstagramRecord] = None
    scheduled_publish_time: Optional[datetime] = None

    # ── Performance Metrics ───────────────────────────────────────────────────
    generation_start_time: Optional[datetime] = None
    generation_end_time: Optional[datetime] = None
    total_generation_seconds: Optional[float] = None
    total_cost_usd: Optional[float] = None    # Estimated API costs

    # ── Metadata ──────────────────────────────────────────────────────────────
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None
    retry_count: int = 0
    tags: list[str] = Field(default_factory=list)

    def to_mongo(self) -> dict:
        """Serialize to MongoDB-friendly dict."""
        d = self.model_dump()
        d["_id"] = self.episode_id
        return d

    @classmethod
    def from_mongo(cls, data: dict) -> "EpisodeDoc":
        data.pop("_id", None)
        return cls(**data)


# =============================================================================
# PIPELINE RUN DOCUMENT  (tracks each scheduler run)
# =============================================================================
class PipelineRunDoc(BaseModel):
    run_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    episodes_generated: int = 0
    episodes_published: int = 0
    episodes_failed: int = 0
    total_duration_seconds: Optional[float] = None
    triggered_by: str = "scheduler"    # scheduler | manual | github_actions
    error_message: Optional[str] = None

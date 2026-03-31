"""
Captain Raccoon — MongoDB Repository
All database read/write operations for episodes and pipeline runs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import structlog
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection

from captain_raccoon.config.settings import get_settings
from captain_raccoon.database.models import EpisodeDoc, EpisodeStatus, PipelineRunDoc

log = structlog.get_logger(__name__)


class EpisodeRepository:
    """CRUD operations for Episode documents."""

    COLLECTION = "episodes"

    def __init__(self):
        self._settings = get_settings()
        self._client = MongoClient(self._settings.mongodb_uri)
        self._db = self._client[self._settings.mongodb_database]
        self._col: Collection = self._db[self.COLLECTION]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._col.create_index("episode_id", unique=True)
        self._col.create_index("status")
        self._col.create_index("created_at")
        self._col.create_index([("created_at", DESCENDING)])

    # ─────────────────────────────────────────────────────────────────────────
    # CREATE / UPDATE
    # ─────────────────────────────────────────────────────────────────────────
    def save(self, episode: EpisodeDoc) -> None:
        """Insert or replace episode document."""
        doc = episode.to_mongo()
        doc["updated_at"] = datetime.now(timezone.utc)
        self._col.replace_one(
            {"_id": episode.episode_id},
            doc,
            upsert=True,
        )
        log.debug("repository.saved", episode_id=episode.episode_id, status=episode.status)

    def update_status(self, episode_id: str, status: EpisodeStatus, error: Optional[str] = None) -> None:
        """Update only the status + timestamp fields."""
        update = {
            "$set": {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc),
            }
        }
        if error:
            update["$set"]["error_message"] = error
            update["$inc"] = {"retry_count": 1}
        self._col.update_one({"_id": episode_id}, update)
        log.info("repository.status_updated", episode_id=episode_id, status=status)

    def update_scene_image(self, episode_id: str, scene_number: int, image_data: dict) -> None:
        """Update image fields for a specific scene (for live progress tracking)."""
        self._col.update_one(
            {"_id": episode_id, "scenes.scene_number": scene_number},
            {
                "$set": {
                    f"scenes.$.image_url": image_data.get("url"),
                    f"scenes.$.image_local_path": image_data.get("local_path"),
                    f"scenes.$.image_provider": image_data.get("provider"),
                    f"scenes.$.image_generation_ms": image_data.get("ms"),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

    def update_youtube_record(self, episode_id: str, record: dict) -> None:
        self._col.update_one(
            {"_id": episode_id},
            {"$set": {"youtube": record, "updated_at": datetime.now(timezone.utc)}},
        )

    def update_instagram_record(self, episode_id: str, record: dict) -> None:
        self._col.update_one(
            {"_id": episode_id},
            {"$set": {"instagram": record, "updated_at": datetime.now(timezone.utc)}},
        )

    # ─────────────────────────────────────────────────────────────────────────
    # READ
    # ─────────────────────────────────────────────────────────────────────────
    def get(self, episode_id: str) -> Optional[EpisodeDoc]:
        doc = self._col.find_one({"_id": episode_id})
        return EpisodeDoc.from_mongo(doc) if doc else None

    def get_by_status(self, status: EpisodeStatus, limit: int = 10) -> list[EpisodeDoc]:
        docs = self._col.find({"status": status.value}).sort("created_at", DESCENDING).limit(limit)
        return [EpisodeDoc.from_mongo(d) for d in docs]

    def get_recent(self, limit: int = 20) -> list[EpisodeDoc]:
        docs = self._col.find().sort("created_at", DESCENDING).limit(limit)
        return [EpisodeDoc.from_mongo(d) for d in docs]

    def get_queue(self) -> list[EpisodeDoc]:
        """Get all episodes waiting to be generated."""
        return self.get_by_status(EpisodeStatus.QUEUED)

    def count_by_status(self) -> dict:
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        result = self._col.aggregate(pipeline)
        return {row["_id"]: row["count"] for row in result}

    def get_published_count(self) -> int:
        return self._col.count_documents({"status": EpisodeStatus.PUBLISHED.value})


class PipelineRunRepository:
    """CRUD operations for pipeline run logs."""

    COLLECTION = "pipeline_runs"

    def __init__(self):
        self._settings = get_settings()
        self._client = MongoClient(self._settings.mongodb_uri)
        self._db = self._client[self._settings.mongodb_database]
        self._col: Collection = self._db[self.COLLECTION]

    def save(self, run: PipelineRunDoc) -> None:
        doc = run.model_dump()
        doc["_id"] = run.run_id
        self._col.replace_one({"_id": run.run_id}, doc, upsert=True)

    def get_recent(self, limit: int = 10) -> list[PipelineRunDoc]:
        docs = self._col.find().sort("started_at", DESCENDING).limit(limit)
        return [PipelineRunDoc(**{k: v for k, v in d.items() if k != "_id"}) for d in docs]

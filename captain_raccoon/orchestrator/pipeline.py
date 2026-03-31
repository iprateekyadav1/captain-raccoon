"""
Captain Raccoon — Main Pipeline Orchestrator
Coordinates all engines from story generation to final publish.
Checkpoints every stage to MongoDB so it can resume after any failure.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import structlog

from captain_raccoon.config.settings import get_settings
from captain_raccoon.database.models import EpisodeDoc, EpisodeStatus, SceneDoc
from captain_raccoon.database.repository import EpisodeRepository, PipelineRunRepository
from captain_raccoon.database.models import PipelineRunDoc
from captain_raccoon.engines.assembly_engine import AssemblyEngine
from captain_raccoon.engines.audio_engine import AudioEngine
from captain_raccoon.engines.image_engine import ImageEngine
from captain_raccoon.engines.scene_engine import SceneEngine
from captain_raccoon.engines.story_engine import StoryEngine, EpisodeScript
from captain_raccoon.engines.video_engine import VideoEngine
from captain_raccoon.monitoring.setup import track_metric, capture_exception, timed
from captain_raccoon.publishers.instagram_publisher import InstagramPublisher
from captain_raccoon.publishers.youtube_publisher import YouTubePublisher
from captain_raccoon.utils.logger import bind_episode_context, clear_context, log_timing
from captain_raccoon.utils.storage import StorageManager

log = structlog.get_logger(__name__)


def _make_episode_id() -> str:
    """Generate a human-readable episode ID."""
    now = datetime.now(timezone.utc)
    short_uuid = str(uuid.uuid4())[:8]
    return f"ep_{now.strftime('%Y%m%d')}_{short_uuid}"


# =============================================================================
# PIPELINE ORCHESTRATOR
# =============================================================================
class CaptainRaccoonPipeline:
    """
    Full end-to-end pipeline:

    1. 📝 Story Generation   → Claude API writes episode script
    2. 🎨 Scene Enrichment   → Scene → image/video/audio prompts
    3. 🖼  Image Generation   → FLUX.1 per scene (concurrent)
    4. 🎬 Video Generation   → Wan 2.1 i2v per scene (concurrent)
    5. 🔊 Audio Generation   → Azure TTS narration + music mix
    6. ✂️  Assembly           → FFmpeg stitch + subtitles + thumbnail
    7. ☁️  Upload             → Azure/DO Spaces for storage
    8. 📲 Publish            → YouTube + Instagram
    9. 📊 Track              → MongoDB + Datadog metrics
    """

    def __init__(self):
        self._settings = get_settings()
        self._episode_repo = EpisodeRepository()
        self._run_repo = PipelineRunRepository()
        self._story_engine = StoryEngine()
        self._scene_engine = SceneEngine()
        self._image_engine = ImageEngine()
        self._video_engine = VideoEngine()
        self._audio_engine = AudioEngine()
        self._assembly_engine = AssemblyEngine()
        self._youtube = YouTubePublisher()
        self._instagram = InstagramPublisher()
        self._storage = StorageManager()

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────
    def run_single(
        self,
        topic: Optional[str] = None,
        theme: Optional[str] = None,
        publish: bool = True,
        episode_id: Optional[str] = None,
    ) -> EpisodeDoc:
        """
        Generate + publish one complete episode.

        Args:
            topic:      Optional episode topic hint
            theme:      Optional content pillar
            publish:    If False, assembles but skips publishing
            episode_id: Resume a specific episode (after failure)
        """
        ep_id = episode_id or _make_episode_id()
        bind_episode_context(ep_id)

        log.info("pipeline.start", episode_id=ep_id, topic=topic, theme=theme)
        track_metric("pipeline.run_started", 1)

        # Check if we're resuming a partial episode
        existing = self._episode_repo.get(ep_id)
        if existing and existing.status == EpisodeStatus.ASSEMBLED:
            log.info("pipeline.resuming_publish", episode_id=ep_id)
            return self._run_publish_stage(existing)

        try:
            # Stage 1: Story
            with log_timing("pipeline.stage.story", episode_id=ep_id):
                script, episode_doc = self._run_story_stage(ep_id, topic, theme)

            # Stage 2–4: Scene enrichment + images + videos (concurrent)
            with log_timing("pipeline.stage.visuals", episode_id=ep_id):
                rich_scenes, images, clips = self._run_visual_stages(episode_doc, script)

            # Stage 5: Audio
            with log_timing("pipeline.stage.audio", episode_id=ep_id):
                audio = self._run_audio_stage(ep_id, rich_scenes)

            # Stage 6: Assembly
            with log_timing("pipeline.stage.assembly", episode_id=ep_id):
                assembled = self._run_assembly_stage(ep_id, clips, audio, rich_scenes)

            # Update episode doc with assembled paths
            episode_doc.final_video_path = str(assembled.final_path)
            episode_doc.thumbnail_path = str(assembled.thumbnail_path)
            episode_doc.total_duration_seconds = assembled.duration_seconds
            episode_doc.status = EpisodeStatus.ASSEMBLED
            episode_doc.generation_end_time = datetime.now(timezone.utc)
            if episode_doc.generation_start_time:
                delta = (episode_doc.generation_end_time - episode_doc.generation_start_time)
                episode_doc.total_generation_seconds = delta.total_seconds()
            self._episode_repo.save(episode_doc)

            # Stage 7–8: Upload + Publish
            if publish:
                episode_doc = self._run_publish_stage(episode_doc, script=script)

            track_metric("pipeline.run_completed", 1)
            log.info("pipeline.complete", episode_id=ep_id, status=episode_doc.status)
            return episode_doc

        except Exception as e:
            capture_exception(e, {"episode_id": ep_id})
            track_metric("pipeline.run_failed", 1)
            log.error("pipeline.failed", episode_id=ep_id, error=str(e))
            self._episode_repo.update_status(ep_id, EpisodeStatus.FAILED, error=str(e))
            raise

        finally:
            clear_context()

    def run_batch(self, count: int = 3, publish: bool = True) -> list[EpisodeDoc]:
        """Generate + publish multiple episodes covering different themes."""
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        pipeline_run = PipelineRunDoc(run_id=run_id, triggered_by="batch")
        self._run_repo.save(pipeline_run)

        results = []
        for i in range(count):
            try:
                ep = self.run_single(publish=publish)
                results.append(ep)
                pipeline_run.episodes_generated += 1
                if ep.status == EpisodeStatus.PUBLISHED:
                    pipeline_run.episodes_published += 1
            except Exception as e:
                pipeline_run.episodes_failed += 1
                log.error("pipeline.batch_item_failed", index=i, error=str(e))

        pipeline_run.completed_at = datetime.now(timezone.utc)
        self._run_repo.save(pipeline_run)
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE RUNNERS
    # ─────────────────────────────────────────────────────────────────────────
    def _run_story_stage(
        self, ep_id: str, topic: Optional[str], theme: Optional[str]
    ):
        """Stage 1: Generate script + initialize Episode document."""
        script = self._story_engine.generate(topic=topic, theme=theme)

        # Build EpisodeDoc from script
        episode_doc = EpisodeDoc(
            episode_id=ep_id,
            title=script.title,
            logline=script.logline,
            theme=script.theme,
            hook=script.hook,
            call_to_action=script.call_to_action,
            hashtags=script.hashtags,
            youtube_title=script.youtube_title,
            youtube_description=script.youtube_description,
            instagram_caption=script.instagram_caption,
            total_duration_seconds=script.total_duration_seconds,
            word_count=script.word_count,
            status=EpisodeStatus.GENERATING,
            generation_start_time=datetime.now(timezone.utc),
            scenes=[
                SceneDoc(
                    scene_number=s.scene_number,
                    narration=s.narration,
                    visual_description=s.visual_description,
                    emotion=s.emotion,
                    setting=s.setting,
                    action=s.action,
                    duration_seconds=s.duration_seconds,
                )
                for s in script.scenes
            ],
        )
        self._episode_repo.save(episode_doc)
        log.info("pipeline.story_done", title=script.title, scenes=len(script.scenes))
        return script, episode_doc

    def _run_visual_stages(self, episode_doc: EpisodeDoc, script: EpisodeScript):
        """Stages 2–4: Scene enrichment + concurrent image + video generation."""
        # Stage 2: Enrich scenes with prompts
        rich_scenes = self._scene_engine.enrich(script)

        # Stage 3: Generate images (concurrent)
        image_prompts = [rs.image_prompt for rs in rich_scenes]
        images = asyncio.run(
            self._image_engine.generate_all(image_prompts, episode_doc.episode_id)
        )

        # Update DB with image paths
        self._episode_repo.update_status(episode_doc.episode_id, EpisodeStatus.IMAGES_DONE)
        for img in images:
            self._episode_repo.update_scene_image(
                episode_doc.episode_id,
                img.scene_number,
                {
                    "url": img.remote_url,
                    "local_path": str(img.local_path),
                    "provider": img.provider,
                    "ms": img.generation_time_ms,
                },
            )

        log.info("pipeline.images_done", count=len(images))

        # Stage 4: Animate images to video clips (concurrent)
        video_prompts = [rs.video_prompt for rs in rich_scenes]
        clips = asyncio.run(
            self._video_engine.animate_all(images, video_prompts, episode_doc.episode_id)
        )
        self._episode_repo.update_status(episode_doc.episode_id, EpisodeStatus.VIDEOS_DONE)
        log.info("pipeline.videos_done", count=len(clips))

        return rich_scenes, images, clips

    def _run_audio_stage(self, ep_id: str, rich_scenes):
        """Stage 5: Generate narration + mix music."""
        audio = self._audio_engine.generate_episode_audio(
            rich_scenes=rich_scenes,
            episode_id=ep_id,
            music_genre="motivational",
        )
        self._episode_repo.update_status(ep_id, EpisodeStatus.AUDIO_DONE)
        log.info("pipeline.audio_done", duration=audio.total_duration_seconds)
        return audio

    def _run_assembly_stage(self, ep_id: str, clips, audio, rich_scenes):
        """Stage 6: Stitch all assets into final video."""
        assembled = self._assembly_engine.assemble(
            episode_id=ep_id,
            clips=clips,
            audio=audio,
            rich_scenes=rich_scenes,
        )
        log.info(
            "pipeline.assembly_done",
            path=str(assembled.final_path),
            duration=assembled.duration_seconds,
            size_mb=round(assembled.file_size_bytes / 1_048_576, 1),
        )
        return assembled

    def _run_publish_stage(
        self,
        episode_doc: EpisodeDoc,
        script: Optional[EpisodeScript] = None,
    ) -> EpisodeDoc:
        """Stages 7–8: Upload to cloud + publish to YouTube + Instagram."""
        ep_id = episode_doc.episode_id
        final_path = Path(episode_doc.final_video_path)
        thumbnail_path = Path(episode_doc.thumbnail_path) if episode_doc.thumbnail_path else None

        from captain_raccoon.engines.assembly_engine import AssembledEpisode
        import os
        assembled = AssembledEpisode(
            episode_id=ep_id,
            final_path=final_path,
            thumbnail_path=thumbnail_path or final_path,
            duration_seconds=episode_doc.total_duration_seconds,
            resolution="1080x1920",
            file_size_bytes=final_path.stat().st_size if final_path.exists() else 0,
        )

        # Rebuild script-like object from episode_doc if not provided
        if not script:
            script = self._rebuild_script_from_doc(episode_doc)

        # YouTube
        try:
            yt_result = self._youtube.publish(assembled, script)
            if yt_result:
                self._episode_repo.update_youtube_record(
                    ep_id,
                    {
                        "video_id": yt_result.video_id,
                        "video_url": yt_result.video_url,
                        "title": yt_result.title,
                        "privacy_status": yt_result.privacy_status,
                        "published_at": datetime.now(timezone.utc),
                        "upload_duration_seconds": yt_result.upload_time_seconds,
                    },
                )
                track_metric("pipeline.youtube_published", 1)
        except Exception as e:
            log.error("pipeline.youtube_failed", error=str(e))
            capture_exception(e)

        # Instagram (15 minutes after YouTube for algorithm reasons)
        try:
            ig_result = self._instagram.publish(assembled, script)
            if ig_result:
                self._episode_repo.update_instagram_record(
                    ep_id,
                    {
                        "media_id": ig_result.media_id,
                        "post_url": ig_result.post_url,
                        "published_at": datetime.now(timezone.utc),
                        "upload_duration_seconds": ig_result.upload_time_seconds,
                    },
                )
                track_metric("pipeline.instagram_published", 1)
        except Exception as e:
            log.error("pipeline.instagram_failed", error=str(e))
            capture_exception(e)

        self._episode_repo.update_status(ep_id, EpisodeStatus.PUBLISHED)
        episode_doc.status = EpisodeStatus.PUBLISHED
        log.info("pipeline.published", episode_id=ep_id)
        return episode_doc

    def _rebuild_script_from_doc(self, doc: EpisodeDoc) -> EpisodeScript:
        """Reconstruct a minimal EpisodeScript from an EpisodeDoc for publishing."""
        from captain_raccoon.engines.story_engine import EpisodeScript, Scene
        scenes = [
            Scene(
                scene_number=s.scene_number,
                title=f"Scene {s.scene_number}",
                narration=s.narration,
                visual_description=s.visual_description,
                emotion=s.emotion,
                duration_seconds=s.duration_seconds,
                setting=s.setting,
                action=s.action,
            )
            for s in doc.scenes
        ]
        return EpisodeScript(
            title=doc.title,
            logline=doc.logline,
            theme=doc.theme,
            hook=doc.hook,
            scenes=scenes,
            call_to_action=doc.call_to_action,
            hashtags=doc.hashtags,
            youtube_title=doc.youtube_title,
            youtube_description=doc.youtube_description,
            instagram_caption=doc.instagram_caption,
            total_duration_seconds=doc.total_duration_seconds,
            word_count=doc.word_count,
        )

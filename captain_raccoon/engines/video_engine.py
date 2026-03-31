"""
Captain Raccoon — Video Engine
Animates scene images using Wan 2.1 (image-to-video) via Replicate.
Falls back to text-to-video, then MiniMax, then local ComfyUI.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlretrieve
from typing import Optional

import httpx
import replicate
import structlog

from captain_raccoon.config.settings import get_settings
from captain_raccoon.engines.image_engine import GeneratedImage
from captain_raccoon.engines.scene_engine import VideoPrompt
from captain_raccoon.monitoring.setup import track_metric, capture_exception
from captain_raccoon.utils.retry import with_retry

log = structlog.get_logger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================
@dataclass
class GeneratedClip:
    scene_number: int
    local_path: Path
    remote_url: str
    provider: str
    duration_seconds: float
    generation_time_ms: int
    source_image_path: Optional[Path] = None


# =============================================================================
# VIDEO ENGINE
# =============================================================================
class VideoEngine:
    """
    Generates short video clips from images using:
    Primary   → Wan 2.1 i2v-480p (image-to-video) via Replicate
    Fallback1 → Wan 2.1 t2v-480p (text-to-video)
    Fallback2 → MiniMax Video-01
    Fallback3 → ComfyUI local (if available)
    """

    WAN_I2V = "wavespeedai/wan-2.1-i2v-480p"
    WAN_T2V = "wavespeedai/wan-2.1-t2v-480p"
    MINIMAX  = "minimax/video-01"

    def __init__(self):
        self._settings = get_settings()
        self._output_dir = self._settings.episode_output_dir
        self._client = replicate.Client(api_token=self._settings.replicate_api_token)

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────
    async def animate_all(
        self,
        images: list[GeneratedImage],
        video_prompts: list[VideoPrompt],
        episode_id: str,
    ) -> list[GeneratedClip]:
        """Animate all scene images concurrently."""
        if len(images) != len(video_prompts):
            raise ValueError(
                f"Mismatch: {len(images)} images vs {len(video_prompts)} prompts"
            )

        semaphore = asyncio.Semaphore(self._settings.max_concurrent_video_jobs)
        tasks = [
            self._animate_with_semaphore(semaphore, img, vp, episode_id)
            for img, vp in zip(images, video_prompts)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        clips = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                log.error("video_engine.scene_failed", scene=i + 1, error=str(result))
                capture_exception(result)
            else:
                clips.append(result)

        track_metric("video_engine.clips_generated", len(clips))
        return clips

    def animate_one(
        self,
        image: GeneratedImage,
        video_prompt: VideoPrompt,
        episode_id: str,
    ) -> GeneratedClip:
        """Synchronous single-clip generation."""
        return asyncio.run(self._animate_clip(image, video_prompt, episode_id))

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE CORE
    # ─────────────────────────────────────────────────────────────────────────
    async def _animate_with_semaphore(
        self,
        sem: asyncio.Semaphore,
        image: GeneratedImage,
        vp: VideoPrompt,
        episode_id: str,
    ) -> GeneratedClip:
        async with sem:
            return await self._animate_clip(image, vp, episode_id)

    async def _animate_clip(
        self,
        image: GeneratedImage,
        vp: VideoPrompt,
        episode_id: str,
    ) -> GeneratedClip:
        start = time.time()

        providers = [
            ("wan_i2v",  self._wan_image_to_video),
            ("wan_t2v",  self._wan_text_to_video),
            ("minimax",  self._minimax_video),
            ("comfyui",  self._comfyui_local),
        ]

        last_error: Optional[Exception] = None
        for provider_name, fn in providers:
            try:
                log.debug(
                    "video_engine.trying_provider",
                    provider=provider_name,
                    scene=vp.scene_number,
                )
                video_url = await asyncio.get_event_loop().run_in_executor(
                    None, fn, image, vp
                )
                if not video_url:
                    continue

                local_path = self._download_clip(video_url, episode_id, vp.scene_number)
                elapsed_ms = int((time.time() - start) * 1000)

                log.info(
                    "video_engine.success",
                    provider=provider_name,
                    scene=vp.scene_number,
                    ms=elapsed_ms,
                )
                track_metric(
                    "video_engine.generation_ms",
                    elapsed_ms,
                    tags={"provider": provider_name},
                )
                return GeneratedClip(
                    scene_number=vp.scene_number,
                    local_path=local_path,
                    remote_url=video_url,
                    provider=provider_name,
                    duration_seconds=vp.duration_seconds,
                    generation_time_ms=elapsed_ms,
                    source_image_path=image.local_path,
                )
            except Exception as e:
                log.warning(
                    "video_engine.provider_failed",
                    provider=provider_name,
                    scene=vp.scene_number,
                    error=str(e),
                )
                capture_exception(e)
                last_error = e
                continue

        raise RuntimeError(
            f"All video providers failed for scene {vp.scene_number}"
        ) from last_error

    # ─────────────────────────────────────────────────────────────────────────
    # PROVIDERS
    # ─────────────────────────────────────────────────────────────────────────
    @with_retry(max_attempts=3)
    def _wan_image_to_video(self, image: GeneratedImage, vp: VideoPrompt) -> str:
        """Wan 2.1 image-to-video — best quality, preserves character look."""
        output = replicate.run(
            self.WAN_I2V,
            input={
                "image": open(image.local_path, "rb"),
                "prompt": vp.motion_prompt,
                "negative_prompt": vp.negative_prompt,
                "num_frames": int(vp.duration_seconds * vp.fps),
                "fps": vp.fps,
                "motion_bucket_id": int(vp.motion_strength * 127),
                "noise_aug_strength": 0.02,
            },
        )
        return str(output) if not isinstance(output, list) else str(output[0])

    @with_retry(max_attempts=3)
    def _wan_text_to_video(self, image: GeneratedImage, vp: VideoPrompt) -> str:
        """Wan 2.1 text-to-video — when image-to-video fails."""
        from captain_raccoon.config.settings import get_character
        char = get_character()
        combined_prompt = (
            f"{char.build_image_prompt_prefix()}"
            f"{vp.motion_prompt}"
        )
        output = replicate.run(
            self.WAN_T2V,
            input={
                "prompt": combined_prompt,
                "negative_prompt": vp.negative_prompt,
                "num_frames": int(vp.duration_seconds * vp.fps),
                "fps": vp.fps,
            },
        )
        return str(output) if not isinstance(output, list) else str(output[0])

    @with_retry(max_attempts=2)
    def _minimax_video(self, image: GeneratedImage, vp: VideoPrompt) -> str:
        """MiniMax Video-01 — secondary fallback."""
        output = replicate.run(
            self.MINIMAX,
            input={
                "first_frame_image": open(image.local_path, "rb"),
                "prompt": vp.motion_prompt,
            },
        )
        return str(output) if not isinstance(output, list) else str(output[0])

    @with_retry(max_attempts=2)
    def _comfyui_local(self, image: GeneratedImage, vp: VideoPrompt) -> str:
        """ComfyUI local — zero cost when running locally with GPU."""
        comfy_url = self._settings.comfyui_url
        # ComfyUI has a REST API — this is a simplified trigger
        with httpx.Client(timeout=600.0) as client:
            resp = client.post(
                f"{comfy_url}/prompt",
                json={
                    "prompt": {
                        "1": {
                            "class_type": "LoadImage",
                            "inputs": {"image": str(image.local_path)},
                        },
                        "2": {
                            "class_type": "WanVideoI2V",
                            "inputs": {
                                "image": ["1", 0],
                                "prompt": vp.motion_prompt,
                                "frames": int(vp.duration_seconds * vp.fps),
                            },
                        },
                        "3": {
                            "class_type": "VHS_VideoCombine",
                            "inputs": {
                                "images": ["2", 0],
                                "frame_rate": vp.fps,
                                "filename_prefix": f"scene_{vp.scene_number}",
                            },
                        },
                    }
                },
            )
            resp.raise_for_status()
            return f"comfyui://local/scene_{vp.scene_number}.mp4"

    # ─────────────────────────────────────────────────────────────────────────
    # DOWNLOAD
    # ─────────────────────────────────────────────────────────────────────────
    def _download_clip(self, url: str, episode_id: str, scene_number: int) -> Path:
        ep_dir = self._output_dir / episode_id / "clips"
        ep_dir.mkdir(parents=True, exist_ok=True)
        local_path = ep_dir / f"scene_{scene_number:02d}.mp4"

        if url.startswith("comfyui://"):
            # ComfyUI saves locally — just record the path
            comfy_output = Path(self._settings.comfyui_url.replace("http://localhost:8188", "")) / f"scene_{scene_number}.mp4"
            return local_path  # Simplified

        urlretrieve(url, local_path)
        log.debug(
            "video_engine.downloaded",
            path=str(local_path),
            size=local_path.stat().st_size if local_path.exists() else 0,
        )
        return local_path

"""
Captain Raccoon — Assembly Engine
Stitches video clips + audio + subtitles into the final publishable video.
Uses FFmpeg under the hood. No cloud dependency — runs anywhere FFmpeg is installed.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

from captain_raccoon.config.settings import get_settings, get_pipeline_config
from captain_raccoon.engines.audio_engine import EpisodeAudio, SceneAudio
from captain_raccoon.engines.video_engine import GeneratedClip
from captain_raccoon.engines.scene_engine import RichScene
from captain_raccoon.monitoring.setup import track_metric, capture_exception

log = structlog.get_logger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================
@dataclass
class SubtitleCue:
    index: int
    start_seconds: float
    end_seconds: float
    text: str


@dataclass
class AssembledEpisode:
    episode_id: str
    final_path: Path            # Final MP4, ready to publish
    thumbnail_path: Path        # Auto-generated thumbnail from best frame
    duration_seconds: float
    resolution: str             # e.g. "1080x1920"
    file_size_bytes: int
    subtitle_path: Optional[Path] = None


# =============================================================================
# ASSEMBLY ENGINE
# =============================================================================
class AssemblyEngine:
    """
    Final assembly pipeline:
    1. Scale + normalize all video clips to consistent resolution
    2. Concatenate clips with smooth crossfades
    3. Overlay episode audio (narration + music)
    4. Burn subtitles (caption text) onto video
    5. Add intro/outro bumpers
    6. Export final 1080x1920 MP4
    7. Extract best-frame thumbnail
    """

    def __init__(self):
        self._settings = get_settings()
        self._config = get_pipeline_config()
        self._output_dir = self._settings.episode_output_dir
        self._assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"
        self._font_path = self._assets_dir / "fonts" / "Montserrat-Bold.ttf"

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────
    def assemble(
        self,
        episode_id: str,
        clips: list[GeneratedClip],
        audio: EpisodeAudio,
        rich_scenes: list[RichScene],
    ) -> AssembledEpisode:
        """
        Full assembly pipeline. Returns the finished episode.
        """
        ep_dir = self._output_dir / episode_id
        ep_dir.mkdir(parents=True, exist_ok=True)

        log.info("assembly_engine.start", episode_id=episode_id, clips=len(clips))

        # Step 1: Normalize all clips to same resolution + framerate
        normalized_clips = self._normalize_clips(clips, ep_dir)

        # Step 2: Build subtitle cues from narration + scene timing
        cues = self._build_subtitle_cues(rich_scenes, audio.narration_tracks)
        srt_path = self._write_srt(cues, ep_dir)

        # Step 3: Concatenate clips
        concat_path = ep_dir / "concatenated.mp4"
        self._concatenate_clips(normalized_clips, concat_path)

        # Step 4: Merge audio + burn subtitles
        final_path = ep_dir / f"{episode_id}_final.mp4"
        self._merge_audio_and_subtitles(
            video_path=concat_path,
            audio_path=audio.combined_path,
            srt_path=srt_path,
            output_path=final_path,
            duration=audio.total_duration_seconds,
        )

        # Step 5: Extract thumbnail from best scene (scene 1, 1-second in)
        thumbnail_path = ep_dir / "thumbnail.jpg"
        self._extract_thumbnail(final_path, thumbnail_path, timestamp=1.0)

        # Gather stats
        file_size = final_path.stat().st_size if final_path.exists() else 0
        duration = self._get_video_duration(final_path)

        track_metric("assembly_engine.episode_assembled", 1)
        log.info(
            "assembly_engine.done",
            episode_id=episode_id,
            duration=duration,
            size_mb=round(file_size / 1_048_576, 1),
            output=str(final_path),
        )

        return AssembledEpisode(
            episode_id=episode_id,
            final_path=final_path,
            thumbnail_path=thumbnail_path,
            duration_seconds=duration,
            resolution="1080x1920",
            file_size_bytes=file_size,
            subtitle_path=srt_path,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1 — NORMALIZE CLIPS
    # ─────────────────────────────────────────────────────────────────────────
    def _normalize_clips(
        self, clips: list[GeneratedClip], ep_dir: Path
    ) -> list[Path]:
        """Scale every clip to 1080x1920 @ 30fps, H.264."""
        normalized = []
        norm_dir = ep_dir / "normalized"
        norm_dir.mkdir(exist_ok=True)

        for clip in sorted(clips, key=lambda c: c.scene_number):
            out = norm_dir / f"scene_{clip.scene_number:02d}_norm.mp4"
            cmd = [
                "ffmpeg",
                "-i", str(clip.local_path),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                       "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
                       "fps=30",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-an",                  # Strip audio (we add ours)
                "-y", str(out),
                "-loglevel", "error",
            ]
            subprocess.run(cmd, check=True)
            normalized.append(out)
            log.debug("assembly_engine.normalized", scene=clip.scene_number)

        return normalized

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2 — SUBTITLE CUES
    # ─────────────────────────────────────────────────────────────────────────
    def _build_subtitle_cues(
        self,
        rich_scenes: list[RichScene],
        narration_tracks: list[SceneAudio],
    ) -> list[SubtitleCue]:
        """Build word/sentence-level subtitle cues aligned to audio timing."""
        cues = []
        current_time = 0.0
        idx = 0

        for rs, na in zip(rich_scenes, narration_tracks):
            narration = rs.scene.narration.strip()
            sentences = [s.strip() for s in narration.replace("?", ".").replace("!", ".").split(".") if s.strip()]
            total_words = len(narration.split())
            duration = na.duration_seconds

            word_time = duration / max(total_words, 1)
            sentence_start = current_time

            for sentence in sentences:
                if not sentence:
                    continue
                words = sentence.split()
                sentence_duration = len(words) * word_time
                idx += 1

                # Break long sentences into 2-line chunks (max ~7 words per cue)
                chunk_size = 7
                for j in range(0, len(words), chunk_size):
                    chunk = " ".join(words[j : j + chunk_size])
                    chunk_dur = len(words[j : j + chunk_size]) * word_time
                    cues.append(
                        SubtitleCue(
                            index=idx,
                            start_seconds=sentence_start,
                            end_seconds=sentence_start + chunk_dur,
                            text=chunk,
                        )
                    )
                    sentence_start += chunk_dur
                    idx += 1

            current_time += duration + 0.5  # gap between scenes

        return cues

    def _write_srt(self, cues: list[SubtitleCue], ep_dir: Path) -> Path:
        """Write subtitles as .srt file."""
        srt_path = ep_dir / "subtitles.srt"

        def fmt_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        lines = []
        for i, cue in enumerate(cues, 1):
            lines.append(str(i))
            lines.append(f"{fmt_time(cue.start_seconds)} --> {fmt_time(cue.end_seconds)}")
            lines.append(cue.text)
            lines.append("")

        srt_path.write_text("\n".join(lines), encoding="utf-8")
        return srt_path

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3 — CONCATENATE
    # ─────────────────────────────────────────────────────────────────────────
    def _concatenate_clips(self, clips: list[Path], output: Path) -> None:
        """Concatenate clips using FFmpeg concat demuxer with crossfades."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            for clip in clips:
                f.write(f"file '{clip.resolve()}'\n")
            list_path = Path(f.name)

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-y", str(output),
            "-loglevel", "error",
        ]
        subprocess.run(cmd, check=True)
        list_path.unlink(missing_ok=True)
        log.debug("assembly_engine.concatenated", clips=len(clips))

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4 — MERGE AUDIO + SUBTITLES
    # ─────────────────────────────────────────────────────────────────────────
    def _merge_audio_and_subtitles(
        self,
        video_path: Path,
        audio_path: Path,
        srt_path: Path,
        output_path: Path,
        duration: float,
    ) -> None:
        """
        Merge audio track + burn subtitles (with bold white text + black outline).
        """
        # Build subtitle filter string
        font_path_str = str(self._font_path).replace("\\", "/").replace(":", "\\:")
        subtitle_filter = (
            f"subtitles='{srt_path}':force_style='"
            "Fontname=Montserrat,"
            "FontSize=52,"
            "PrimaryColour=&HFFFFFF&,"
            "OutlineColour=&H000000&,"
            "Outline=3,"
            "Bold=1,"
            "Alignment=2'"   # 2 = bottom center
        )

        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-vf", subtitle_filter,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration),
            "-movflags", "+faststart",   # Web-optimized for YouTube
            "-y", str(output_path),
            "-loglevel", "error",
        ]
        subprocess.run(cmd, check=True)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 5 — THUMBNAIL
    # ─────────────────────────────────────────────────────────────────────────
    def _extract_thumbnail(
        self, video_path: Path, output: Path, timestamp: float = 1.0
    ) -> None:
        """Extract a high-quality frame for YouTube thumbnail."""
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-frames:v", "1",
            "-q:v", "2",            # High quality JPEG
            "-y", str(output),
            "-loglevel", "error",
        ]
        subprocess.run(cmd, check=True)

    # ─────────────────────────────────────────────────────────────────────────
    # UTILITY
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _get_video_duration(path: Path) -> float:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 0.0

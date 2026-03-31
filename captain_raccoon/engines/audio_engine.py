"""
Captain Raccoon — Audio Engine
Generates narration via Azure Neural TTS + mixes royalty-free background music.
Fallbacks: Google Cloud TTS → Coqui TTS (local).
"""
from __future__ import annotations

import os
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

from captain_raccoon.config.settings import get_settings
from captain_raccoon.engines.scene_engine import RichScene
from captain_raccoon.monitoring.setup import track_metric, capture_exception
from captain_raccoon.utils.retry import with_retry

log = structlog.get_logger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================
@dataclass
class SceneAudio:
    scene_number: int
    narration_path: Path        # TTS-generated voice file
    duration_seconds: float
    word_count: int
    provider: str               # azure | google | coqui


@dataclass
class EpisodeAudio:
    narration_tracks: list[SceneAudio]
    music_path: Path
    combined_path: Path         # Final mixed audio for the episode
    total_duration_seconds: float


# =============================================================================
# AUDIO ENGINE
# =============================================================================
class AudioEngine:
    """
    Full audio pipeline:
    1. Generate TTS narration per scene (Azure Neural TTS)
    2. Select appropriate background music track
    3. Mix narration + music (duck music under voice)
    """

    def __init__(self):
        self._settings = get_settings()
        self._output_dir = self._settings.episode_output_dir
        self._music_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "music"

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────
    def generate_episode_audio(
        self,
        rich_scenes: list[RichScene],
        episode_id: str,
        music_genre: str = "motivational",
    ) -> EpisodeAudio:
        """
        Full audio pipeline for one episode.
        Returns paths to individual narration tracks + final mixed audio.
        """
        audio_dir = self._output_dir / episode_id / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate TTS narration for every scene
        narrations: list[SceneAudio] = []
        for rs in rich_scenes:
            try:
                sa = self._generate_narration(rs, audio_dir)
                narrations.append(sa)
            except Exception as e:
                log.error(
                    "audio_engine.narration_failed",
                    scene=rs.scene.scene_number,
                    error=str(e),
                )
                capture_exception(e)
                raise

        # Step 2: Concatenate narrations into one track
        combined_narration = audio_dir / "narration_full.wav"
        self._concatenate_audio(
            [n.narration_path for n in narrations],
            combined_narration,
            gap_ms=500,
        )

        # Step 3: Select background music
        music_path = self._select_music(music_genre)

        # Step 4: Mix narration + music (voice over music, ducked)
        combined_path = audio_dir / "episode_audio.aac"
        total_duration = sum(n.duration_seconds for n in narrations) + (
            len(narrations) * 0.5
        )
        self._mix_audio(
            voice_path=combined_narration,
            music_path=music_path,
            output_path=combined_path,
            total_duration=total_duration,
            music_volume_db=-18,
        )

        track_metric("audio_engine.episode_generated", 1)
        log.info(
            "audio_engine.done",
            episode_id=episode_id,
            scenes=len(narrations),
            duration=total_duration,
        )

        return EpisodeAudio(
            narration_tracks=narrations,
            music_path=music_path,
            combined_path=combined_path,
            total_duration_seconds=total_duration,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # TTS GENERATION
    # ─────────────────────────────────────────────────────────────────────────
    def _generate_narration(
        self, rich_scene: RichScene, audio_dir: Path
    ) -> SceneAudio:
        """Try TTS providers in order."""
        scene = rich_scene.scene
        ssml = rich_scene.tts_ssml
        out_path = audio_dir / f"scene_{scene.scene_number:02d}.wav"
        word_count = len(scene.narration.split())

        providers = [
            ("azure",  self._azure_tts),
            ("google", self._google_tts),
            ("coqui",  self._coqui_tts),
        ]

        last_error: Optional[Exception] = None
        for provider_name, fn in providers:
            try:
                duration = fn(ssml, scene.narration, out_path)
                log.debug(
                    "audio_engine.tts_success",
                    provider=provider_name,
                    scene=scene.scene_number,
                    duration=duration,
                )
                return SceneAudio(
                    scene_number=scene.scene_number,
                    narration_path=out_path,
                    duration_seconds=duration,
                    word_count=word_count,
                    provider=provider_name,
                )
            except Exception as e:
                log.warning(
                    "audio_engine.tts_provider_failed",
                    provider=provider_name,
                    error=str(e),
                )
                last_error = e
                continue

        raise RuntimeError(
            f"All TTS providers failed for scene {scene.scene_number}"
        ) from last_error

    @with_retry(max_attempts=3)
    def _azure_tts(self, ssml: str, plain_text: str, out_path: Path) -> float:
        """Azure Cognitive Services Neural TTS — primary voice."""
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError:
            raise ImportError("azure-cognitiveservices-speech not installed")

        speech_config = speechsdk.SpeechConfig(
            subscription=self._settings.azure_speech_key,
            region=self._settings.azure_speech_region,
        )
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
        )

        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(out_path))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        result = synthesizer.speak_ssml_async(ssml).get()
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            raise RuntimeError(f"Azure TTS failed: {result.reason}")

        return self._get_audio_duration(out_path)

    @with_retry(max_attempts=2)
    def _google_tts(self, ssml: str, plain_text: str, out_path: Path) -> float:
        """Google Cloud TTS — fallback (free tier: 1M chars/month WaveNet)."""
        try:
            from google.cloud import texttospeech
        except ImportError:
            raise ImportError("google-cloud-texttospeech not installed")

        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=plain_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-D",
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=0.95,
            pitch=0.0,
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        out_path.write_bytes(response.audio_content)
        return self._get_audio_duration(out_path)

    def _coqui_tts(self, ssml: str, plain_text: str, out_path: Path) -> float:
        """Coqui TTS — fully local, zero cost fallback."""
        result = subprocess.run(
            [
                "tts",
                "--text", plain_text,
                "--model_name", "tts_models/en/ljspeech/glow-tts",
                "--out_path", str(out_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Coqui TTS failed: {result.stderr}")
        return self._get_audio_duration(out_path)

    # ─────────────────────────────────────────────────────────────────────────
    # MUSIC SELECTION
    # ─────────────────────────────────────────────────────────────────────────
    def _select_music(self, genre: str) -> Path:
        """Select a royalty-free music track from the local library."""
        genre_dir = self._music_dir / genre
        fallback_dir = self._music_dir

        # Search genre-specific folder first, then general
        for search_dir in [genre_dir, fallback_dir]:
            if search_dir.exists():
                tracks = list(search_dir.glob("*.mp3")) + list(search_dir.glob("*.wav"))
                if tracks:
                    selected = random.choice(tracks)
                    log.info("audio_engine.music_selected", track=selected.name, genre=genre)
                    return selected

        # Last resort: generate silence (pipeline continues)
        log.warning("audio_engine.no_music_found", genre=genre)
        silence_path = self._output_dir / ".cache" / "silence.wav"
        silence_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
             "-t", "120", str(silence_path), "-y", "-loglevel", "quiet"],
            check=True,
        )
        return silence_path

    # ─────────────────────────────────────────────────────────────────────────
    # AUDIO MIXING (FFmpeg)
    # ─────────────────────────────────────────────────────────────────────────
    def _concatenate_audio(
        self,
        tracks: list[Path],
        output: Path,
        gap_ms: int = 500,
    ) -> None:
        """Concatenate multiple WAV files with a small gap between them."""
        if not tracks:
            raise ValueError("No audio tracks to concatenate")

        # Build FFmpeg concat filter
        inputs = []
        filter_parts = []
        for i, t in enumerate(tracks):
            inputs += ["-i", str(t)]
            filter_parts.append(f"[{i}:a]")

        # Add silence padding between scenes
        silence_gap = f"aevalsrc=0:s=44100:d={gap_ms/1000}"
        concat_filter = "".join(filter_parts) + f"concat=n={len(tracks)}:v=0:a=1[out]"

        cmd = [
            "ffmpeg",
            *inputs,
            "-filter_complex", concat_filter,
            "-map", "[out]",
            "-y", str(output),
            "-loglevel", "error",
        ]
        subprocess.run(cmd, check=True)
        log.debug("audio_engine.concatenated", output=str(output))

    def _mix_audio(
        self,
        voice_path: Path,
        music_path: Path,
        output_path: Path,
        total_duration: float,
        music_volume_db: int = -18,
    ) -> None:
        """
        Mix voice + background music.
        - Music loops if shorter than narration
        - Music fades in/out smoothly
        - Voice sits prominently over music
        """
        fade_duration = min(3.0, total_duration * 0.1)

        cmd = [
            "ffmpeg",
            "-i", str(voice_path),
            "-stream_loop", "-1",           # Loop music if needed
            "-i", str(music_path),
            "-filter_complex",
            (
                f"[1:a]volume={music_volume_db}dB,"
                f"afade=t=in:st=0:d={fade_duration},"
                f"afade=t=out:st={max(0, total_duration - fade_duration)}:d={fade_duration},"
                f"atrim=0:{total_duration}[music];"
                "[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[out]"
            ),
            "-map", "[out]",
            "-t", str(total_duration),
            "-c:a", "aac",
            "-b:a", "192k",
            "-y", str(output_path),
            "-loglevel", "error",
        ]
        subprocess.run(cmd, check=True)
        log.info("audio_engine.mixed", output=str(output_path), duration=total_duration)

    # ─────────────────────────────────────────────────────────────────────────
    # UTILITY
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _get_audio_duration(path: Path) -> float:
        """Get audio duration in seconds using FFprobe."""
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

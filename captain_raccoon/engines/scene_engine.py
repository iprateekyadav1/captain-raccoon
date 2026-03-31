"""
Captain Raccoon — Scene Engine
Transforms raw EpisodeScript scenes into rich, model-ready prompts
for image generation (FLUX.1) and video generation (Wan 2.1).
"""
from __future__ import annotations

from dataclasses import dataclass

import structlog

from captain_raccoon.config.settings import get_character
from captain_raccoon.engines.story_engine import Scene, EpisodeScript

log = structlog.get_logger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================
@dataclass
class ImagePrompt:
    """Ready-to-send prompt for FLUX.1 / SDXL."""
    positive: str
    negative: str
    width: int = 1080
    height: int = 1920          # 9:16 portrait for Reels/Shorts
    scene_number: int = 1
    emotion: str = "calm"


@dataclass
class VideoPrompt:
    """Ready-to-send prompt for Wan 2.1 image-to-video."""
    motion_prompt: str           # Describes HOW things move
    negative_prompt: str
    duration_seconds: float = 5.0
    fps: int = 24
    motion_strength: float = 0.7
    scene_number: int = 1


@dataclass
class RichScene:
    """A scene with all generation prompts attached."""
    scene: Scene
    image_prompt: ImagePrompt
    video_prompt: VideoPrompt
    tts_ssml: str                # Azure TTS SSML markup


# =============================================================================
# SCENE ENGINE
# =============================================================================
class SceneEngine:
    """
    Takes an EpisodeScript and enriches every scene with:
    - FLUX.1 image prompt (character-consistent, emotion-aware)
    - Wan 2.1 video motion prompt (cinematic, natural movement)
    - Azure TTS SSML (pacing, pauses, emphasis)
    """

    # Emotion → lighting / color grading mapping
    EMOTION_VISUALS = {
        "happy":       "warm golden sunlight, lens flare, vibrant colors, cheerful atmosphere",
        "sad":         "overcast soft light, muted blues and grays, gentle rain, melancholic",
        "tense":       "dramatic side lighting, deep shadows, high contrast, suspenseful",
        "calm":        "soft diffused light, pastel tones, peaceful, serene atmosphere",
        "funny":       "bright cartoonish lighting, saturated colors, comedic energy",
        "determined":  "low angle shot, warm backlighting, heroic, motivational energy",
        "reflective":  "blue hour dusk light, quiet, introspective, long shadows",
    }

    # Emotion → camera / movement mapping for video
    EMOTION_CAMERA = {
        "happy":       "gentle push-in, slight upward tilt, warm handheld energy",
        "sad":         "slow pull-back, static wide shot, still and quiet",
        "tense":       "shaky handheld, quick pan, nervous energy",
        "calm":        "smooth slow dolly, wide establishing, serene pan",
        "funny":       "quick zoom-in for reaction, bounce cut energy",
        "determined":  "upward tilt reveal, slow push-in, epic slow motion",
        "reflective":  "static lockdown, very slow drift, contemplative",
    }

    # Emotion → TTS speaking style
    EMOTION_VOICE_STYLE = {
        "happy":       "cheerful",
        "sad":         "sad",
        "tense":       "excited",
        "calm":        "gentle",
        "funny":       "cheerful",
        "determined":  "empathetic",
        "reflective":  "gentle",
    }

    def __init__(self):
        self._character = get_character()
        self._char_prefix = self._character.build_image_prompt_prefix()
        self._negative_base = self._character.negative_prompt

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────
    def enrich(self, script: EpisodeScript) -> list[RichScene]:
        """Enrich all scenes in an episode script."""
        rich_scenes = []
        for scene in script.scenes:
            rich = self._enrich_scene(scene)
            rich_scenes.append(rich)
            log.debug(
                "scene_engine.enriched",
                scene=scene.scene_number,
                emotion=scene.emotion,
            )
        log.info("scene_engine.done", total=len(rich_scenes))
        return rich_scenes

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE BUILDERS
    # ─────────────────────────────────────────────────────────────────────────
    def _enrich_scene(self, scene: Scene) -> RichScene:
        image_prompt = self._build_image_prompt(scene)
        video_prompt = self._build_video_prompt(scene)
        ssml = self._build_ssml(scene)
        return RichScene(
            scene=scene,
            image_prompt=image_prompt,
            video_prompt=video_prompt,
            tts_ssml=ssml,
        )

    def _build_image_prompt(self, scene: Scene) -> ImagePrompt:
        emotion = scene.emotion.lower()
        lighting = self.EMOTION_VISUALS.get(emotion, self.EMOTION_VISUALS["calm"])

        # Core subject
        subject = (
            f"{self._char_prefix}"
            f"{scene.visual_description.strip()}, "
            f"{scene.action}, "
        )

        # Setting context
        setting_ctx = f"set in {scene.setting}, "

        # Mood and technical quality
        quality = (
            f"{lighting}, "
            "masterpiece quality, 4K, sharp focus, cinematic composition, "
            "rule of thirds, dramatic depth of field, "
            "professional color grading, suitable for short-form social media"
        )

        positive = subject + setting_ctx + quality

        # Scene-specific negative additions
        extra_neg = ""
        if emotion == "funny":
            extra_neg = ", overly dark, grim, depressing"
        elif emotion == "sad":
            extra_neg = ", happy cheerful, bright neon"

        negative = self._negative_base + extra_neg

        return ImagePrompt(
            positive=positive,
            negative=negative,
            width=1080,
            height=1920,
            scene_number=scene.scene_number,
            emotion=emotion,
        )

    def _build_video_prompt(self, scene: Scene) -> VideoPrompt:
        emotion = scene.emotion.lower()
        camera = self.EMOTION_CAMERA.get(emotion, self.EMOTION_CAMERA["calm"])

        # Describe the motion naturally
        action_motion = self._action_to_motion(scene.action)

        motion = (
            f"{action_motion}. "
            f"{camera}. "
            f"Subtle environmental animation: leaves rustling, light shifting, "
            f"atmospheric particles floating. "
            f"Cinematic {emotion} mood. Smooth, professional animation quality."
        )

        negative = (
            "static, frozen, no movement, jittery, flickering, artifact, "
            "glitch, morphing faces, distortion, low quality, blurry"
        )

        return VideoPrompt(
            motion_prompt=motion,
            negative_prompt=negative,
            duration_seconds=5.0,
            fps=24,
            motion_strength=self._emotion_to_motion_strength(emotion),
            scene_number=scene.scene_number,
        )

    def _build_ssml(self, scene: Scene) -> str:
        """Build Azure TTS SSML for natural, emotional narration."""
        char = self._character
        emotion = scene.emotion.lower()
        voice_style = self.EMOTION_VOICE_STYLE.get(emotion, "gentle")
        voice_name = char.voice_name

        # Add natural pauses at sentence boundaries
        narration = scene.narration.strip()
        narration = narration.replace(". ", '. <break time="400ms"/> ')
        narration = narration.replace("... ", '... <break time="600ms"/> ')
        narration = narration.replace("? ", '? <break time="350ms"/> ')
        narration = narration.replace("! ", '! <break time="350ms"/> ')

        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
    xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
  <voice name="{voice_name}">
    <mstts:express-as style="{voice_style}" styledegree="1.2">
      <prosody rate="-5%" pitch="+0Hz">
        {narration}
      </prosody>
    </mstts:express-as>
  </voice>
</speak>"""
        return ssml

    # ─────────────────────────────────────────────────────────────────────────
    # UTILITY
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _action_to_motion(action: str) -> str:
        """Convert a static action description to motion language."""
        action_lower = action.lower()
        if any(w in action_lower for w in ["walk", "run", "mov"]):
            return f"Character walks forward naturally, {action}"
        if any(w in action_lower for w in ["sit", "rest", "lean"]):
            return f"Character breathes gently, subtle idle sway, {action}"
        if any(w in action_lower for w in ["look", "gaze", "star"]):
            return f"Character's eyes move naturally, head tilts slightly, {action}"
        if any(w in action_lower for w in ["speak", "talk", "say"]):
            return f"Character gestures naturally while speaking, expressive, {action}"
        return f"Subtle natural movement, {action}"

    @staticmethod
    def _emotion_to_motion_strength(emotion: str) -> float:
        mapping = {
            "happy": 0.75,
            "sad": 0.45,
            "tense": 0.85,
            "calm": 0.40,
            "funny": 0.80,
            "determined": 0.70,
            "reflective": 0.35,
        }
        return mapping.get(emotion, 0.60)

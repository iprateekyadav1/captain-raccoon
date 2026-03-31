"""
Captain Raccoon — Centralized Settings
All config loaded from environment variables (via Doppler in production).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Project root ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT_DIR / "captain_raccoon" / "config"
ASSETS_DIR = ROOT_DIR / "assets"
OUTPUT_DIR = ROOT_DIR / "output"


# =============================================================================
# SETTINGS MODEL
# =============================================================================
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment ───────────────────────────────────────────────────────────
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")

    # ── Anthropic / Claude ────────────────────────────────────────────────────
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-opus-4-5", alias="CLAUDE_MODEL")
    claude_fallback_model: str = Field(default="claude-haiku-4-5", alias="CLAUDE_FALLBACK_MODEL")

    # ── Replicate (Image + Video generation) ──────────────────────────────────
    replicate_api_token: str = Field(..., alias="REPLICATE_API_TOKEN")

    # ── HuggingFace (Fallback generation) ─────────────────────────────────────
    huggingface_api_token: str = Field(default="", alias="HUGGINGFACE_API_TOKEN")

    # ── Azure (TTS + Storage) ─────────────────────────────────────────────────
    azure_speech_key: str = Field(..., alias="AZURE_SPEECH_KEY")
    azure_speech_region: str = Field(default="eastus", alias="AZURE_SPEECH_REGION")
    azure_storage_connection_string: str = Field(
        default="", alias="AZURE_STORAGE_CONNECTION_STRING"
    )
    azure_storage_container: str = Field(
        default="captain-raccoon-assets", alias="AZURE_STORAGE_CONTAINER"
    )
    azure_tts_voice: str = Field(default="en-US-GuyNeural", alias="AZURE_TTS_VOICE")
    azure_tts_style: str = Field(default="cheerful", alias="AZURE_TTS_STYLE")

    # ── DigitalOcean Spaces (Fallback Storage) ─────────────────────────────────
    do_spaces_key: str = Field(default="", alias="DO_SPACES_KEY")
    do_spaces_secret: str = Field(default="", alias="DO_SPACES_SECRET")
    do_spaces_bucket: str = Field(default="captain-raccoon", alias="DO_SPACES_BUCKET")
    do_spaces_region: str = Field(default="nyc3", alias="DO_SPACES_REGION")
    do_spaces_endpoint: str = Field(
        default="https://nyc3.digitaloceanspaces.com", alias="DO_SPACES_ENDPOINT"
    )

    # ── MongoDB Atlas ─────────────────────────────────────────────────────────
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_database: str = Field(default="captain_raccoon", alias="MONGODB_DATABASE")

    # ── YouTube ───────────────────────────────────────────────────────────────
    youtube_client_id: str = Field(default="", alias="YOUTUBE_CLIENT_ID")
    youtube_client_secret: str = Field(default="", alias="YOUTUBE_CLIENT_SECRET")
    youtube_refresh_token: str = Field(default="", alias="YOUTUBE_REFRESH_TOKEN")
    youtube_channel_id: str = Field(default="", alias="YOUTUBE_CHANNEL_ID")

    # ── Instagram ─────────────────────────────────────────────────────────────
    instagram_access_token: str = Field(default="", alias="INSTAGRAM_ACCESS_TOKEN")
    instagram_account_id: str = Field(default="", alias="INSTAGRAM_ACCOUNT_ID")

    # ── Monitoring ────────────────────────────────────────────────────────────
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    datadog_api_key: str = Field(default="", alias="DATADOG_API_KEY")
    newrelic_license_key: str = Field(default="", alias="NEW_RELIC_LICENSE_KEY")

    # ── Local fallback config ─────────────────────────────────────────────────
    automatic1111_url: str = Field(
        default="http://localhost:7860", alias="AUTOMATIC1111_URL"
    )
    comfyui_url: str = Field(default="http://localhost:8188", alias="COMFYUI_URL")

    # ── Pipeline behaviour ────────────────────────────────────────────────────
    max_concurrent_image_jobs: int = Field(default=3, alias="MAX_CONCURRENT_IMAGE_JOBS")
    max_concurrent_video_jobs: int = Field(default=2, alias="MAX_CONCURRENT_VIDEO_JOBS")
    episode_output_dir: Path = Field(default=OUTPUT_DIR / "episodes")
    asset_cache_dir: Path = Field(default=OUTPUT_DIR / ".cache")

    @field_validator("episode_output_dir", "asset_cache_dir", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        p = Path(v)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


# =============================================================================
# CHARACTER PROFILE LOADER
# =============================================================================
class CharacterProfile:
    """Loads and exposes Captain Raccoon's character YAML."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or CONFIG_DIR / "character.yaml"
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        with open(self._path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

    @property
    def name(self) -> str:
        return self._data["identity"]["name"]

    @property
    def visual_description(self) -> str:
        return self._data["identity"]["visual"]["base_description"].strip()

    @property
    def art_style(self) -> str:
        return self._data["identity"]["visual"]["art_style"]

    @property
    def lora_trigger(self) -> str:
        return self._data["identity"]["visual"].get("lora_trigger", "")

    @property
    def negative_prompt(self) -> str:
        return self._data["identity"]["visual"]["negative_prompt"].strip()

    @property
    def personality_traits(self) -> list[str]:
        return self._data["identity"]["personality"]["core_traits"]

    @property
    def voice_name(self) -> str:
        return self._data["identity"]["voice"]["azure_voice_name"]

    @property
    def storytelling_style(self) -> str:
        return self._data["identity"]["voice"]["storytelling_style"].strip()

    @property
    def content_pillars(self) -> list[str]:
        return self._data["identity"]["content_pillars"]

    @property
    def world_description(self) -> str:
        return self._data["identity"]["world"]["description"].strip()

    @property
    def episode_format(self) -> dict:
        return self._data["identity"]["episode_format"]

    def build_character_system_prompt(self) -> str:
        """Returns a complete system prompt string for Claude story generation."""
        traits = "\n".join(f"  - {t}" for t in self.personality_traits)
        pillars = "\n".join(f"  - {p}" for p in self.content_pillars)
        return f"""You are a creative writer for "{self.name}", an animated short-form video series.

CHARACTER: {self.name}
{self.visual_description}

PERSONALITY:
{traits}

STORYTELLING STYLE:
{self.storytelling_style}

WORLD: {self.world_description}

CONTENT PILLARS (themes to explore):
{pillars}

RULES:
- Every story must feel personal and real, not like a generic motivational poster
- Never use corporate buzzwords (synergy, hustle culture, grind, etc.)
- Always end with hope, never false positivity
- Stories should resonate with humans despite the animal kingdom setting
- Keep narration conversational — Captain Raccoon talks TO the viewer, not AT them
- Max {self.episode_format['target_duration_seconds']} seconds when read aloud at {self.episode_format.get('words_per_minute', 140)} words/minute
"""

    def build_image_prompt_prefix(self) -> str:
        """Character-consistent prefix for every image generation prompt."""
        trigger = f"{self.lora_trigger}, " if self.lora_trigger else ""
        return f"{trigger}{self.visual_description}, {self.art_style}, "


# =============================================================================
# PIPELINE CONFIG LOADER
# =============================================================================
class PipelineConfig:
    """Loads pipeline.yaml with environment variable interpolation."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or CONFIG_DIR / "pipeline.yaml"
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        with open(self._path, "r", encoding="utf-8") as f:
            raw = f.read()
        # Simple env var substitution: ${VAR:default}
        import re
        def replace_env(match: re.Match) -> str:
            parts = match.group(1).split(":", 1)
            key = parts[0]
            default = parts[1] if len(parts) > 1 else ""
            return os.environ.get(key, default)
        interpolated = re.sub(r"\$\{([^}]+)\}", replace_env, raw)
        self._data = yaml.safe_load(interpolated)

    def get(self, *keys: str, default=None):
        """Safely traverse nested YAML keys."""
        node = self._data
        for key in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(key, default)
            if node is None:
                return default
        return node


# =============================================================================
# CACHED SINGLETONS
# =============================================================================
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def get_character() -> CharacterProfile:
    return CharacterProfile()


@lru_cache(maxsize=1)
def get_pipeline_config() -> PipelineConfig:
    return PipelineConfig()

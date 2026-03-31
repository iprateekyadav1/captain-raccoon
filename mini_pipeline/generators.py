"""
generators.py — Story · Image · Video
Veo 3 primary | LTX-Video (HF free) | Wan 2.1 (Replicate) fallbacks
"""
from __future__ import annotations
import base64, json, re, time
from pathlib import Path
from urllib.request import urlretrieve

import anthropic, httpx, replicate
import google.generativeai as genai

import config

# ── initialise clients once ──────────────────────────────────────────────────
_claude  = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
genai.configure(api_key=config.GOOGLE_AI_API_KEY)
_replicate = replicate.Client(api_token=config.REPLICATE_API_TOKEN)


# =============================================================================
# 1. STORY + SCRIPT
# =============================================================================
CHARACTER_PROMPT = """You are writing for Captain Raccoon (Mike, 24) — entrepreneur,
podcast host. Midnight-dark fur, sharp eyes, dry sarcastic wit. Confident but genuinely
kind. Hates fluff. Loves philosophy, psychology, Batman. His bat friend Charles is chaos
to his order. Content: worldly affairs, self-discipline, clear thinking.

Return ONLY valid JSON:
{
  "title": "short punchy title",
  "hook": "3-second scroll-stopper opening line",
  "scenes": [
    {"narration": "...", "visual": "cinematic scene description for image gen", "emotion": "calm|happy|determined|reflective|funny"}
  ],
  "cta": "soft closing line",
  "caption": "Instagram caption <150 chars + 3 hashtags",
  "yt_title": "YouTube title <70 chars with emoji"
}"""

def generate_story(topic: str | None = None) -> dict:
    """Claude → structured episode JSON."""
    topic = topic or "the discipline nobody talks about"
    resp = _claude.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"Write a Captain Raccoon short-form video script about: {topic}\n4-5 scenes, ~60s total.\n\n{CHARACTER_PROMPT}"
        }]
    )
    raw = resp.content[0].text
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError("No JSON in Claude response")
    return json.loads(m.group(0))


# =============================================================================
# 2. IMAGE GENERATION  (FLUX.1-dev → schnell fallback)
# =============================================================================
CAP_PREFIX = (
    "anthropomorphic raccoon, midnight-dark fur, sharp determined eyes, "
    "black mask markings, confident posture, well-dressed, wry expression, "
    "3D Pixar-quality render, cinematic lighting, "
)
NEG = "ugly, deformed, blurry, low quality, bad anatomy, scary"

def generate_image(visual: str, scene_num: int, episode_dir: Path) -> Path:
    """FLUX.1-dev → FLUX.1-schnell. Returns local PNG path."""
    prompt = CAP_PREFIX + visual
    out = episode_dir / f"scene_{scene_num:02d}.png"

    for model in ["black-forest-labs/flux-dev", "black-forest-labs/flux-schnell"]:
        try:
            result = _replicate.run(
                model,
                input={
                    "prompt": prompt,
                    "negative_prompt": NEG,
                    "width": 1080, "height": 1920,
                    "num_inference_steps": 28 if "dev" in model else 4,
                }
            )
            url = str(result[0]) if isinstance(result, list) else str(result)
            urlretrieve(url, out)
            print(f"  ✅ Image scene {scene_num} [{model.split('/')[-1]}]")
            return out
        except Exception as e:
            print(f"  ⚠️  {model} failed: {e}")

    # HuggingFace free inference fallback
    return _image_hf_fallback(prompt, out)

def _image_hf_fallback(prompt: str, out: Path) -> Path:
    resp = httpx.post(
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
        headers={"Authorization": f"Bearer {config.HF_API_TOKEN}"},
        json={"inputs": prompt},
        timeout=120,
    )
    resp.raise_for_status()
    out.write_bytes(resp.content)
    print(f"  ✅ Image [HuggingFace fallback]")
    return out


# =============================================================================
# 3. VIDEO GENERATION
#    Veo 3.1 (Google AI Studio) → LTX-Video (HF free) → Wan 2.1 (Replicate)
# =============================================================================
VEO_MODEL = "veo-3.0-generate-preview"          # Google AI Studio
LTX_HF    = "Lightricks/LTX-Video"              # Free HF inference
WAN_I2V   = "wavespeedai/wan-2.1-i2v-480p"      # Replicate fallback

def generate_video(
    image_path: Path,
    motion_prompt: str,
    scene_num: int,
    episode_dir: Path,
) -> Path:
    """Veo 3.1 → LTX-Video (HF) → Wan 2.1 (Replicate)."""
    out = episode_dir / f"scene_{scene_num:02d}.mp4"

    # --- Veo 3.1 (Google AI Studio) ---
    try:
        return _veo3(image_path, motion_prompt, out, scene_num)
    except Exception as e:
        print(f"  ⚠️  Veo 3 failed: {e}")

    # --- LTX-Video (HuggingFace, free) ---
    try:
        return _ltx_video_hf(image_path, motion_prompt, out, scene_num)
    except Exception as e:
        print(f"  ⚠️  LTX-Video failed: {e}")

    # --- Wan 2.1 i2v (Replicate, credits) ---
    return _wan_replicate(image_path, motion_prompt, out, scene_num)


def _veo3(image_path: Path, prompt: str, out: Path, n: int) -> Path:
    """
    Google Veo 3.1 via Gemini API.
    Requires: GOOGLE_AI_API_KEY with Veo access (AI Studio → enable video generation)
    """
    from google.generativeai import types as gtypes

    image_b64 = base64.b64encode(image_path.read_bytes()).decode()

    operation = genai.Client().models.generate_video(
        model=VEO_MODEL,
        prompt=prompt,
        image=gtypes.Image(
            image_bytes=base64.b64decode(image_b64),
            mime_type="image/png",
        ),
        config=gtypes.GenerateVideoConfig(
            duration_seconds=5,
            aspect_ratio="9:16",
            number_of_videos=1,
        ),
    )

    # Poll until done
    while not operation.done:
        time.sleep(5)
        operation = operation.refresh()

    video_bytes = operation.result.generated_videos[0].video.video_bytes
    out.write_bytes(video_bytes)
    print(f"  ✅ Video scene {n} [Veo 3.1]")
    return out


def _ltx_video_hf(image_path: Path, prompt: str, out: Path, n: int) -> Path:
    """
    LTX-Video via HuggingFace Inference API — FREE tier.
    Open-source model by Lightricks. No sign-up cost beyond HF account.
    """
    image_b64 = base64.b64encode(image_path.read_bytes()).decode()

    resp = httpx.post(
        f"https://api-inference.huggingface.co/models/{LTX_HF}",
        headers={"Authorization": f"Bearer {config.HF_API_TOKEN}"},
        json={
            "inputs": prompt,
            "parameters": {
                "image": image_b64,
                "num_frames": 121,
                "fps": 24,
                "guidance_scale": 3.0,
            }
        },
        timeout=300,
    )
    resp.raise_for_status()
    out.write_bytes(resp.content)
    print(f"  ✅ Video scene {n} [LTX-Video / HuggingFace free]")
    return out


def _wan_replicate(image_path: Path, prompt: str, out: Path, n: int) -> Path:
    """Wan 2.1 image-to-video via Replicate (starter credits)."""
    result = _replicate.run(
        WAN_I2V,
        input={
            "image": open(image_path, "rb"),
            "prompt": prompt,
            "num_frames": 121,
            "fps": 24,
        }
    )
    url = str(result) if not isinstance(result, list) else str(result[0])
    urlretrieve(url, out)
    print(f"  ✅ Video scene {n} [Wan 2.1 / Replicate]")
    return out

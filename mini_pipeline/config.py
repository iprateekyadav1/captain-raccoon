import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ── AI Keys ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_AI_API_KEY   = os.getenv("GOOGLE_AI_API_KEY", "")       # Veo 3.1 — AI Studio
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")     # FLUX.1 + Wan fallback
HF_API_TOKEN        = os.getenv("HF_API_TOKEN", "")            # Free HF inference

# ── Publish ───────────────────────────────────────────────────────────────────
YT_CLIENT_ID        = os.getenv("YT_CLIENT_ID", "")
YT_CLIENT_SECRET    = os.getenv("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN    = os.getenv("YT_REFRESH_TOKEN", "")
IG_ACCESS_TOKEN     = os.getenv("IG_ACCESS_TOKEN", "")
IG_ACCOUNT_ID       = os.getenv("IG_ACCOUNT_ID", "")

# ── Storage (needed for Instagram's public video URL requirement) ──────────────
AZURE_STORAGE_CONN  = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_CONTAINER     = os.getenv("AZURE_CONTAINER", "captain-raccoon")

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

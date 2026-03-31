# =============================================================================
# Captain Raccoon — Dockerfile
# Multi-stage build: lean production image with FFmpeg
# =============================================================================

FROM python:3.11-slim AS base

# System deps (FFmpeg for video assembly)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dependency layer (cached unless requirements change) ──────────────────────
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Application layer ─────────────────────────────────────────────────────────
FROM deps AS app
COPY . .

# Create output directories
RUN mkdir -p output/episodes output/.cache assets/music assets/fonts assets/overlays

# Non-root user for security
RUN useradd -m -u 1000 raccoon && chown -R raccoon:raccoon /app
USER raccoon

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── Default: run scheduler ────────────────────────────────────────────────────
CMD ["python", "-m", "captain_raccoon.orchestrator.scheduler", "full"]

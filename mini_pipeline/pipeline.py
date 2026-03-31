"""
Captain Raccoon — Mini Pipeline
Story → Images → Videos → Assemble → Upload

Usage:
  python pipeline.py                        # random topic
  python pipeline.py "stoic philosophy"     # specific topic
  python pipeline.py "discipline" --no-publish
"""
from __future__ import annotations
import asyncio, subprocess, sys, uuid
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

import config
from generators import generate_story, generate_image, generate_video
from publishers import upload_youtube, upload_instagram

console = Console()


async def run(topic: str | None = None, publish: bool = True) -> Path:
    ep_id  = str(uuid.uuid4())[:8]
    ep_dir = config.OUTPUT_DIR / ep_id
    ep_dir.mkdir(parents=True)

    console.print(Panel(f"[bold cyan]🦝 Captain Raccoon Mini Pipeline[/bold cyan]\nEpisode: {ep_id}", border_style="cyan"))

    # ── 1. Story ──────────────────────────────────────────────────────────────
    console.print("\n[bold]1/4 — Generating story...[/bold]")
    script = generate_story(topic)
    console.print(f"  ✅ '{script['title']}'  ({len(script['scenes'])} scenes)")

    # ── 2 & 3. Images + Videos (scene by scene) ───────────────────────────────
    video_clips: list[Path] = []
    for i, scene in enumerate(script["scenes"], 1):
        console.print(f"\n[bold]{i}/{len(script['scenes'])} scene — image + video[/bold]")

        img  = generate_image(scene["visual"], i, ep_dir)
        clip = generate_video(img, scene["visual"] + " " + scene["narration"], i, ep_dir)
        video_clips.append(clip)

    # ── 4. Assemble with FFmpeg ───────────────────────────────────────────────
    console.print("\n[bold]4/4 — Assembling video...[/bold]")
    final = _assemble(video_clips, script, ep_dir)
    console.print(f"  ✅ Final → {final}")

    # ── 5. Publish ────────────────────────────────────────────────────────────
    if publish:
        console.print("\n[bold]Publishing...[/bold]")
        _publish(final, script)

    console.print(Panel(f"[green]Done![/green] {script['title']}", border_style="green"))
    return final


# =============================================================================
# ASSEMBLY (FFmpeg — no cloud needed)
# =============================================================================
def _assemble(clips: list[Path], script: dict, ep_dir: Path) -> Path:
    # Write concat list
    list_f = ep_dir / "clips.txt"
    list_f.write_text("\n".join(f"file '{c.resolve()}'" for c in clips))

    raw = ep_dir / "raw.mp4"
    final = ep_dir / "final.mp4"

    # 1. Concat clips
    subprocess.run([
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", str(list_f),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-crf", "22", "-y", str(raw), "-loglevel", "error"
    ], check=True)

    # 2. Write subtitles (simple SRT from narrations)
    srt = _make_srt(script["scenes"], ep_dir)

    # 3. Burn subtitles
    subtitle_filter = f"subtitles='{srt}':force_style='FontSize=50,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=3,Bold=1,Alignment=2'"
    subprocess.run([
        "ffmpeg", "-i", str(raw),
        "-vf", subtitle_filter,
        "-c:v", "libx264", "-crf", "22",
        "-movflags", "+faststart",
        "-y", str(final), "-loglevel", "error"
    ], check=True)

    return final


def _make_srt(scenes: list[dict], ep_dir: Path) -> Path:
    srt = ep_dir / "subs.srt"
    lines, t = [], 0.0
    for i, s in enumerate(scenes, 1):
        words = s["narration"].split()
        dur   = max(2.0, len(words) / 2.2)   # ~132wpm
        lines += [
            str(i),
            f"{_ts(t)} --> {_ts(t + dur)}",
            s["narration"],
            ""
        ]
        t += dur + 0.4
    srt.write_text("\n".join(lines))
    return srt

def _ts(s: float) -> str:
    h, m = int(s // 3600), int((s % 3600) // 60)
    sec, ms = int(s % 60), int((s % 1) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


# =============================================================================
# PUBLISH
# =============================================================================
def _publish(final: Path, script: dict):
    if config.YT_REFRESH_TOKEN:
        try:
            upload_youtube(
                final,
                title=script["yt_title"],
                description=script.get("caption", script["title"]),
                tags=["CaptainRaccoon", "motivation", "philosophy"],
            )
        except Exception as e:
            console.print(f"  [red]YouTube failed: {e}[/red]")

    if config.IG_ACCESS_TOKEN and config.AZURE_STORAGE_CONN:
        try:
            upload_instagram(final, script["caption"])
        except Exception as e:
            console.print(f"  [red]Instagram failed: {e}[/red]")


# =============================================================================
if __name__ == "__main__":
    topic   = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
    publish = "--no-publish" not in sys.argv
    asyncio.run(run(topic=topic, publish=publish))

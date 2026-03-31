"""
Captain Raccoon — CLI: Generate Episode
Run from command line or GitHub Actions.
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from captain_raccoon.monitoring.setup import init_monitoring
from captain_raccoon.orchestrator.pipeline import CaptainRaccoonPipeline
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Generate a Captain Raccoon episode")
    parser.add_argument("--topic", default="", help="Episode topic hint")
    parser.add_argument("--theme", default="", help="Content pillar theme")
    parser.add_argument("--publish", default="true", choices=["true", "false"])
    parser.add_argument("--count", type=int, default=1, help="Number of episodes")
    parser.add_argument("--episode-id", default="", help="Resume specific episode")
    args = parser.parse_args()

    init_monitoring()
    pipeline = CaptainRaccoonPipeline()

    should_publish = args.publish.lower() == "true"
    topic = args.topic or None
    theme = args.theme or None
    episode_id = args.episode_id or None

    console.print(Panel(
        "[bold cyan]🦝 Captain Raccoon Pipeline[/bold cyan]\n"
        f"Episodes: {args.count} | Publish: {should_publish}",
        border_style="cyan"
    ))

    for i in range(args.count):
        console.print(f"\n[bold]Episode {i + 1}/{args.count}[/bold]")
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Generating...", total=None)
                episode = pipeline.run_single(
                    topic=topic,
                    theme=theme,
                    publish=should_publish,
                    episode_id=episode_id,
                )
                progress.update(task, description=f"✅ {episode.title}")

            console.print(f"[green]✅ Done:[/green] {episode.title}")
            if episode.youtube and hasattr(episode.youtube, "video_url"):
                console.print(f"   [blue]YouTube:[/blue] {episode.youtube.get('video_url', 'N/A')}")
            if episode.instagram and hasattr(episode.instagram, "post_url"):
                console.print(f"   [magenta]Instagram:[/magenta] {episode.instagram.get('post_url', 'N/A')}")

        except Exception as e:
            console.print(f"[red]❌ Failed: {e}[/red]")
            if args.count == 1:
                sys.exit(1)


if __name__ == "__main__":
    main()

"""CLI entry-point for realtor-ai-copilot."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from realtor_ai_copilot.analysis.generator import generate_analyses
from realtor_ai_copilot.ingestion.loader import load_listings
from realtor_ai_copilot.matching.scorer import score_listings
from realtor_ai_copilot.models import BuyerProfile
from realtor_ai_copilot.reports.pdf_builder import build_report

app = typer.Typer(
    name="realtor-ai",
    help="AI-powered real estate research assistant for buyer's agents.",
    add_completion=False,
)
console = Console()


def _load_profile(path: Path) -> BuyerProfile:
    with path.open() as fh:
        data = json.load(fh)
    return BuyerProfile(**data)


@app.command()
def run(
    listings: Path = typer.Option(
        ...,
        "--listings",
        "-l",
        help="Path to MLS listings file (.csv or .json)",
        exists=True,
        readable=True,
    ),
    profile: Path = typer.Option(
        ...,
        "--profile",
        "-p",
        help="Path to buyer profile JSON file",
        exists=True,
        readable=True,
    ),
    output: Path = typer.Option(
        Path("report.pdf"),
        "--output",
        "-o",
        help="Output PDF file path",
    ),
    top_n: int = typer.Option(
        10,
        "--top-n",
        "-n",
        help="Include only the top N matches in the report",
        min=1,
    ),
    min_score: float = typer.Option(
        0.0,
        "--min-score",
        "-s",
        help="Exclude listings with a match score below this value (0-100)",
        min=0.0,
        max=100.0,
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="OpenAI API key (defaults to OPENAI_API_KEY env var)",
        envvar="OPENAI_API_KEY",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="OpenAI model to use for analysis",
        envvar="OPENAI_MODEL",
    ),
    no_ai: bool = typer.Option(
        False,
        "--no-ai",
        help="Skip AI analysis (use rule-based summaries only)",
    ),
) -> None:
    """Ingest MLS data, score against a buyer profile, generate analyses, and output a PDF."""
    console.print("\n[bold blue]Realtor AI Copilot[/bold blue]\n")

    # 1. Load listings
    with console.status("Loading MLS listings…"):
        all_listings = load_listings(listings)
    console.print(
        f"[green]✓[/green] Loaded [bold]{len(all_listings)}[/bold] listings"
        f" from {listings.name}"
    )

    # 2. Load profile
    buyer_profile = _load_profile(profile)
    console.print(f"[green]✓[/green] Buyer profile: [bold]{buyer_profile.name}[/bold]")

    # 3. Score & rank
    with console.status("Scoring and ranking listings…"):
        results = score_listings(all_listings, buyer_profile, top_n=top_n, min_score=min_score)
    console.print(f"[green]✓[/green] [bold]{len(results)}[/bold] listings matched")

    # 4. AI analysis
    if not no_ai:
        effective_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        label = "AI" if effective_key else "rule-based"
        with console.status(f"Generating {label} analyses…"):
            generate_analyses(results, buyer_profile, api_key=api_key, model=model)
        console.print(f"[green]✓[/green] Analysis generated ({label})")

    # 5. Print score table to terminal
    tbl = Table(title="Top Matches", show_header=True, header_style="bold blue")
    tbl.add_column("#", width=3)
    tbl.add_column("Address")
    tbl.add_column("Price", justify="right")
    tbl.add_column("Bed/Bath")
    tbl.add_column("Score", justify="right")
    for i, r in enumerate(results, 1):
        score_str = f"[green]{r.score}[/green]" if r.score >= 75 else (
            f"[yellow]{r.score}[/yellow]" if r.score >= 50 else f"[red]{r.score}[/red]"
        )
        tbl.add_row(
            str(i),
            r.listing.full_address,
            f"${r.listing.price:,.0f}",
            f"{r.listing.bedrooms}bd/{r.listing.bathrooms}ba",
            score_str,
        )
    console.print(tbl)

    # 6. Build PDF
    with console.status(f"Building PDF report → {output}…"):
        written = build_report(results, buyer_profile, output)
    console.print(f"[green]✓[/green] PDF written: [bold]{written}[/bold]\n")


if __name__ == "__main__":
    app()

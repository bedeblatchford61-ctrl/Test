#!/usr/bin/env python3
"""CLI entry point for the Commercial Real Estate AI Agent."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from rich.console import Console
from rich.table import Table

from src.agent import CREAgent
from src.config import AgentConfig
from src.models.lead import Lead


console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Commercial Real Estate AI Agent — find and rank seller leads",
    )
    parser.add_argument("--city", default="Austin", help="Target city (default: Austin)")
    parser.add_argument("--state", default="TX", help="Target state code (default: TX)")
    parser.add_argument(
        "--types",
        nargs="+",
        default=["office", "retail", "industrial", "multifamily"],
        help="Property types to target",
    )
    parser.add_argument("--min-value", type=float, default=500_000, help="Minimum property value")
    parser.add_argument("--max-value", type=float, default=50_000_000, help="Maximum property value")
    parser.add_argument("--max-leads", type=int, default=25, help="Max leads to return")
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )
    parser.add_argument("--no-ai", action="store_true", help="Disable AI enrichment")
    parser.add_argument("--data-dir", default="data", help="Directory containing data files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    return parser.parse_args()


def print_leads_table(leads: list[Lead]) -> None:
    if not leads:
        console.print("[yellow]No leads found. Try adjusting your search criteria.[/yellow]")
        return

    table = Table(title="Seller Lead Recommendations", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Priority", width=6)
    table.add_column("Owner", min_width=20)
    table.add_column("Score", justify="right", width=7)
    table.add_column("Properties", justify="right", width=5)
    table.add_column("Est. Value", justify="right", min_width=12)
    table.add_column("Types", min_width=10)
    table.add_column("Top Signals", min_width=30)

    priority_styles = {
        "hot": "[bold red]HOT[/bold red]",
        "warm": "[bold yellow]WARM[/bold yellow]",
        "cold": "[dim]COLD[/dim]",
    }

    for i, lead in enumerate(leads, 1):
        signals = "; ".join(lead.score.reasons[:3])
        table.add_row(
            str(i),
            priority_styles.get(lead.priority.value, lead.priority.value),
            lead.owner.name,
            f"{lead.score.overall:.0f}",
            str(lead.owner.total_properties),
            f"${lead.owner.total_assessed_value:,.0f}",
            ", ".join(lead.owner.property_types),
            signals,
        )

    console.print(table)

    # Print detailed recommendations for hot leads
    hot_leads = [l for l in leads if l.priority.value == "hot"]
    if hot_leads:
        console.print("\n[bold red]--- Hot Lead Details ---[/bold red]\n")
        for lead in hot_leads:
            console.print(f"[bold]{lead.owner.name}[/bold]")
            console.print(f"  Score: {lead.score.overall:.0f}/100")
            console.print(f"  Motivation: {lead.score.motivation:.0f} | Timing: {lead.score.timing:.0f} | Fit: {lead.score.portfolio_fit:.0f} | Deal Size: {lead.score.deal_size:.0f}")
            console.print(f"  Approach: {lead.recommended_approach}")
            if lead.ai_summary:
                console.print(f"  AI Insight: {lead.ai_summary}")
            console.print()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    config = AgentConfig(
        city=args.city,
        state=args.state,
        property_types=args.types,
        min_value=args.min_value,
        max_value=args.max_value,
        max_leads=args.max_leads,
        output_format=args.format,
        enrich_with_ai=not args.no_ai,
        public_records_path=f"{args.data_dir}/sample_properties.json",
        listings_path=f"{args.data_dir}/sample_listings.json",
    )

    agent = CREAgent(config=config)
    leads = agent.run()

    if args.format == "json":
        print(agent.leads_to_json(leads))
    else:
        print_leads_table(leads)


if __name__ == "__main__":
    main()

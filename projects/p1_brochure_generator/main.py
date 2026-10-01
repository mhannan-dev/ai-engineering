"""
Enterprise Brochure Generator - Main CLI Pipeline
Orchestrates Dynamic Crawling, Link Discovery, Token Compression,
and Structured Pydantic Output Generation.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import DEFAULT_MAX_CRAWL_PAGES, DEFAULT_MODEL
from .crawler import EnterpriseWebCrawler
from .generator import BrochureGenerator

console = Console()


def display_compression_stats(stats: dict):
    """Displays token compression metrics using Rich table."""
    table = Table(title="[bold green]Noise Reduction & Token Compression Metrics[/bold green]")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Estimated Original Tokens", f"{stats['original_tokens_est']:,}")
    table.add_row("Compressed Payload Tokens", f"{stats['compressed_tokens_est']:,}")
    table.add_row("Tokens Saved", f"[bold green]{stats['tokens_saved']:,}[/bold green]")
    table.add_row("Compression Ratio", f"[bold yellow]{stats['compression_percentage']}% reduction[/bold yellow]")

    console.print(table)


def save_output(brochure_obj, output_dir: Path, filename_base: str):
    """Saves both raw JSON and formatted Markdown brochure."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{filename_base}_brochure.json"
    md_path = output_dir / f"{filename_base}_brochure.md"

    # Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(brochure_obj.model_dump(), f, indent=2, ensure_ascii=False)

    # Save Markdown
    data = brochure_obj
    md_content = f"""# {data.company.name} - Enterprise Brochure
**Tagline:** {data.company.tagline or 'N/A'}  
**Headquarters:** {data.company.headquarters or 'N/A'} | **Founded:** {data.company.founded_year or 'N/A'}

---

## 🏢 Executive Overview
{data.company.mission_statement}

### Market Verdict
> {data.summary_verdict}

---

## 🎯 Target Audience & Ideal Customer Profile
- **Target Industries:** {', '.join(data.target_audience.primary_industries) if data.target_audience.primary_industries else 'Universal B2B'}
- **ICP:** {data.target_audience.ideal_customer_profile}
- **Key Pain Points Solved:**
"""
    for pp in data.target_audience.core_pain_points:
        md_content += f"  - {pp}\n"

    md_content += "\n---\n\n## 🚀 Product & Service Offerings\n"
    for offering in data.offerings:
        md_content += f"### {offering.name} ({offering.category})\n"
        md_content += f"{offering.description}\n\n"
        if offering.key_features:
            md_content += "**Key Capabilities:**\n"
            for kf in offering.key_features:
                md_content += f"- {kf}\n"
        if offering.target_use_case:
            md_content += f"\n*Primary Use Case:* {offering.target_use_case}\n\n"

    md_content += "\n---\n\n## ⭐ Key Differentiators\n"
    for diff in data.key_differentiators:
        md_content += f"- **{diff.differentiator}**: {diff.business_impact}\n"

    md_content += "\n---\n\n## 💳 Pricing & Engagement Models\n"
    for tier in data.pricing:
        md_content += f"### {tier.tier_name}: {tier.price_info}\n"
        if tier.billing_period:
            md_content += f"*Billing Cycle:* {tier.billing_period}\n"
        for h in tier.highlights:
            md_content += f"- {h}\n"

    md_content += f"""
---

## 📞 Next Steps & Call to Action
- **Primary CTA:** {data.contact_and_cta.primary_cta}
- **Email:** {data.contact_and_cta.contact_email or 'N/A'}
- **Phone:** {data.contact_and_cta.contact_phone or 'N/A'}
- **Link:** {data.contact_and_cta.demo_or_signup_url or 'N/A'}
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    console.print(f"\n[bold green]✓[/bold green] JSON exported to: [cyan]{json_path}[/cyan]")
    console.print(f"[bold green]✓[/bold green] Markdown brochure exported to: [cyan]{md_path}[/cyan]")


async def run_pipeline(url: str, max_pages: int = DEFAULT_MAX_CRAWL_PAGES, model: str = DEFAULT_MODEL):
    """Executes the full pipeline end-to-end."""
    console.print(Panel.fit(
        f"[bold blue]Enterprise Brochure Generator[/bold blue]\nTarget URL: [yellow]{url}[/yellow]\nModel: [green]{model}[/green]",
        border_style="cyan"
    ))

    # Phase 1: Dynamic Web Crawling & Link Discovery
    crawler = EnterpriseWebCrawler()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task1 = progress.add_task("[cyan]Crawling website with dynamic JS rendering...", total=None)
        crawl_result = await crawler.crawl_site(url, max_pages=max_pages)
        progress.update(task1, completed=True, description="[green]Crawling & Link Discovery complete!")

    console.print(f"\n[bold]Pages Crawled:[/bold] {crawl_result['crawled_pages_count']}")
    if crawl_result["discovered_links"]:
        console.print("[bold]Discovered Priority Sub-links:[/bold]")
        for link in crawl_result["discovered_links"]:
            console.print(f"  • [cyan]{link}[/cyan]")

    # Phase 2: Token Compression & Noise Reduction Display
    display_compression_stats(crawl_result["compression_stats"])

    # Phase 3: Structured Generation with Instructor & Auto-Correction
    console.print("\n[cyan]Generating 100% Type-Safe Enterprise Brochure via Instructor...[/cyan]")
    generator = BrochureGenerator(model_name=model)
    
    try:
        brochure = generator.generate_brochure(
            scraped_content=crawl_result["combined_content"],
            company_hint=crawl_result["base_domain"],
        )
    except Exception as e:
        console.print(f"[bold red]Generation Error:[/bold red] {e}")
        return

    # Display Result
    console.print(Panel(
        f"[bold green]Company:[/bold green] {brochure.company.name}\n"
        f"[bold green]Tagline:[/bold green] {brochure.company.tagline or 'N/A'}\n"
        f"[bold green]Offerings Extracted:[/bold green] {len(brochure.offerings)}\n"
        f"[bold green]CTA:[/bold green] {brochure.contact_and_cta.primary_cta}\n\n"
        f"[italic]{brochure.summary_verdict}[/italic]",
        title="[bold yellow]Brochure Summary[/bold yellow]",
        border_style="green"
    ))

    # Save to disk
    domain_slug = crawl_result["base_domain"].replace(".", "_")
    output_dir = Path(__file__).parent / "output"
    save_output(brochure, output_dir, domain_slug)


def main():
    parser = argparse.ArgumentParser(description="Enterprise Brochure Generator CLI")
    parser.add_argument("url", nargs="?", default="https://stripe.com", help="Target enterprise website URL")
    parser.add_argument("--pages", type=int, default=DEFAULT_MAX_CRAWL_PAGES, help="Max internal pages to crawl")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="LLM model identifier")

    args = parser.parse_args()
    asyncio.run(run_pipeline(args.url, max_pages=args.pages, model=args.model))


if __name__ == "__main__":
    main()

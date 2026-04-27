#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "beautifulsoup4",
#   "html2text",
#   "requests",
# ]
# ///
"""
Documentation Scraper CLI

Scrapes technical documentation and converts to LLM-friendly markdown format.

Caching behavior:
  - By default, scrapers use cached HTML responses if available
  - Use --force to clear cache and re-fetch from network
  - Delete .cache/ directory to manually clear all caches

Available scrapers:
  lsp       Language Server Protocol 3.17 specification
  ptx       NVIDIA PTX ISA documentation
  runtime   CUDA Runtime API documentation
  driver    CUDA Driver API documentation

Usage:
  scrape.py <doc_type> [options]
  scrape.py --help
  scrape.py <doc_type> --help

Examples:
  scrape.py lsp                  # Use cache if available
  scrape.py lsp --force          # Re-fetch from network
  scrape.py ptx --output-dir ./docs/ptx
"""

import argparse
import sys
from pathlib import Path

# Import scrapers
from scrapers import APIScraper, LSPScraper, PTXScraper

# Registry of available scrapers
SCRAPERS = {
    "lsp": {
        "class": LSPScraper,
        "requires_api_type": False,
        "default_output": "references/lsp-3.17-docs",
    },
    "ptx": {
        "class": PTXScraper,
        "requires_api_type": False,
        "default_output": "references/ptx-docs",
    },
    "runtime": {
        "class": APIScraper,
        "requires_api_type": True,
        "api_type": "runtime",
        "default_output": "references/cuda-runtime-docs",
    },
    "driver": {
        "class": APIScraper,
        "requires_api_type": True,
        "api_type": "driver",
        "default_output": "references/cuda-driver-docs",
    },
}


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="scrape.py",
        description="Scrape technical documentation to LLM-friendly markdown format.\n\n"
        "Caching:\n"
        "  - By default, uses cached HTML responses if available\n"
        "  - Use --force to clear cache and re-fetch\n"
        "  - Delete .cache/ directory to clear all caches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s lsp                           Use cache if available
  %(prog)s lsp --force                   Clear cache and re-fetch
  %(prog)s ptx --output-dir ./docs       Custom output location
  %(prog)s driver                        Scrape CUDA Driver API

Cache location: .cache/<scraper-name>/

For detailed help on a specific scraper:
  %(prog)s lsp --help
  %(prog)s driver --help
""",
    )

    subparsers = parser.add_subparsers(
        dest="doc_type",
        title="document types",
        description="Available documentation types to scrape",
    )

    # Create subparser for each scraper
    for name, config in SCRAPERS.items():
        sub = subparsers.add_parser(
            name,
            help=f"Scrape {name.upper()} documentation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=config["class"].description,
        )
        sub.add_argument(
            "--output-dir",
            type=Path,
            help=f"Output directory (default: {config['default_output']})",
        )
        sub.add_argument(
            "--force",
            action="store_true",
            help="Clear cache and re-fetch from network",
        )

    return parser


def main() -> None:
    """Main entry point."""
    parser = create_parser()

    # Handle no arguments
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Handle missing doc_type
    if not args.doc_type:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Get scraper config
    config = SCRAPERS[args.doc_type]

    # Set default output directory
    output_dir = args.output_dir or Path(config["default_output"])

    # Create scraper instance
    scraper_class = config["class"]
    if config["requires_api_type"]:
        scraper = scraper_class(
            api_type=config["api_type"],
            output_dir=output_dir,
            force=args.force,
        )
    else:
        scraper = scraper_class(output_dir=output_dir, force=args.force)

    # Run the scraper
    scraper.run()


if __name__ == "__main__":
    main()

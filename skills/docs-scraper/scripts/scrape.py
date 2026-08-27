#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "beautifulsoup4",
#   "html2text",
#   "requests",
#   "rich>=13.0.0",
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
  rust      Rust crate documentation (uses cargo-docs-md)

Usage:
  scrape.py <doc_type> [options]
  scrape.py --help
  scrape.py <doc_type> --help

Examples:
  scrape.py lsp                  # Use cache if available
  scrape.py lsp --force          # Re-fetch from network
  scrape.py rust ratatui         # Scrape Rust crate
  scrape.py rust https://github.com/ratatui/ratatui
"""

import argparse
import sys
from pathlib import Path

# Import scrapers
from scrapers import APIScraper, LSPScraper, PTXScraper, RustScraper, SiteScraper, SkillsScraper

# Registry of available scrapers
SCRAPERS = {
    "lsp": {
        "class": LSPScraper,
        "requires_api_type": False,
        "default_output": "references/lsp-3.17-docs",
        "is_rust": False,
        "is_site": False,
    },
    "ptx": {
        "class": PTXScraper,
        "requires_api_type": False,
        "default_output": "references/ptx-docs",
        "is_rust": False,
        "is_site": False,
    },
    "runtime": {
        "class": APIScraper,
        "requires_api_type": True,
        "api_type": "runtime",
        "default_output": "references/cuda-runtime-docs",
        "is_rust": False,
        "is_site": False,
    },
    "driver": {
        "class": APIScraper,
        "requires_api_type": True,
        "api_type": "driver",
        "default_output": "references/cuda-driver-docs",
        "is_rust": False,
        "is_site": False,
    },
    "rust": {
        "class": RustScraper,
        "default_output": "references/rust-docs",
        "is_rust": True,
        "is_site": False,
    },
    "site": {
        "class": SiteScraper,
        "default_output": "site-output",
        "is_rust": False,
        "is_site": True,
    },
    "skills": {
        "class": SkillsScraper,  # pyright: ignore[reportUnknownMemberType]
        "default_output": ".lsz/tmp/skill-compose",
        "is_rust": False,
        "is_site": False,
        "is_skills": True,
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
  %(prog)s rust ratatui                  Scrape Rust crate by name
  %(prog)s rust https://github.com/ratatui/ratatui
  %(prog)s rust ./my-local-crate

Cache location: .cache/<scraper-name>/

For detailed help on a specific scraper:
  %(prog)s lsp --help
  %(prog)s rust --help
""",
    )

    subparsers = parser.add_subparsers(
        dest="doc_type",
        title="document types",
        description="Available documentation types to scrape",
    )

    # Create subparser for each scraper
    for name, config in SCRAPERS.items():
        if config["is_rust"]:
            # Rust scraper has different arguments
            sub = subparsers.add_parser(
                name,
                help="Scrape Rust crate documentation",
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=config["class"].description,  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            )
            _ = sub.add_argument(
                "target",
                help="Crate name, GitHub URL, docs.rs URL, or local path",
            )
            _ = sub.add_argument(
                "--output-dir",
                type=Path,
                help=f"Output directory (default: {config['default_output']})",
            )
            _ = sub.add_argument(
                "--force",
                action="store_true",
                help="Re-clone repository and regenerate",
            )
            _ = sub.add_argument(
                "--primary-crate",
                help="Primary crate name for workspaces",
            )
            _ = sub.add_argument(
                "--include-deps",
                action="store_true",
                help="Include dependency documentation (default: workspace only)",
            )
            _ = sub.add_argument(
                "--include-examples",
                action="store_true",
                help="Include example crates from workspace (default: library crates only)",
            )
            _ = sub.add_argument(
                "--full-method-docs",
                action="store_true",
                default=True,
                help="Include full method documentation (default: True)",
            )
            _ = sub.add_argument(
                "--exclude-private",
                action="store_true",
                default=True,
                help="Exclude private items (default: True)",
            )
        elif config.get("is_skills"):
            sub = subparsers.add_parser(  # pyright: ignore[reportUnknownMemberType]
                name,
                help="Fetch skills from skill.sh via npx skills mature client for LLM composition",
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=config["class"].description,  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            )
            _ = sub.add_argument(
                "inputs",
                nargs="+",
                help="Skill sources: skill.sh URL, owner/collection/skill, or GitHub repo URL",
            )
            _ = sub.add_argument(
                "--staging",
                type=Path,
                help="Staging root (default: .lsz/tmp/skill-compose)",
            )
            _ = sub.add_argument(
                "--output-dir",
                type=Path,
                help="Alias for --staging",
            )
            _ = sub.add_argument(
                "--run",
                help="Run slug for multi-run isolation (default: single run at staging root)",
            )
            _ = sub.add_argument(
                "--method",
                choices=["auto", "raw", "clone", "npx"],
                default="auto",
                help="Fetch method (default: auto -> npx; raw/clone deprecated, map to npx)",
            )
            _ = sub.add_argument(
                "--force",
                action="store_true",
                help="Clear cache and re-fetch from network",
            )
        elif config.get("is_site"):
            # Site scraper has base_url and urls arguments
            sub = subparsers.add_parser(
                name,
                help="Scrape generic site via llms.txt/sitemap.xml",
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=config["class"].description,  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            )
            _ = sub.add_argument(
                "urls",
                nargs="*",
                help="URLs to fetch (fetch mode). If omitted, uses discovery mode.",
            )
            _ = sub.add_argument(
                "--base-url",
                help="Base URL for discovery mode (finds URLs via llms.txt/sitemap.xml)",
            )
            _ = sub.add_argument(
                "--output-dir",
                type=Path,
                help=f"Output directory (default: {config['default_output']})",
            )
            _ = sub.add_argument(
                "--force",
                action="store_true",
                help="Clear cache and re-fetch from network",
            )
        else:
            # Standard web scrapers
            sub = subparsers.add_parser(
                name,
                help=f"Scrape {name.upper()} documentation",
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=config["class"].description,  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            )
            _ = sub.add_argument(
                "--output-dir",
                type=Path,
                help=f"Output directory (default: {config['default_output']})",
            )
            _ = sub.add_argument(
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
    output_dir = args.output_dir or Path(config["default_output"])  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]

    # Create scraper instance
    if config.get("is_skills"):
        staging = (
            getattr(args, "staging", None)
            or getattr(args, "output_dir", None)
            or Path(config["default_output"])
        )  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        scraper = config["class"](  # pyright: ignore[reportUnknownMemberType, reportCallIssue]
            inputs=getattr(args, "inputs", None),
            staging=staging,
            run=getattr(args, "run", None),
            output_dir=getattr(args, "output_dir", None),
            method=getattr(args, "method", "auto"),
            force=args.force,
        )
    elif config["is_rust"]:
        scraper = config["class"](
            target=args.target,
            output_dir=output_dir,
            force=args.force,
            primary_crate=getattr(args, "primary_crate", None),
            include_deps=getattr(args, "include_deps", False),
            include_examples=getattr(args, "include_examples", False),
            full_method_docs=getattr(args, "full_method_docs", True),
            exclude_private=getattr(args, "exclude_private", True),
        )
    elif config.get("is_site"):
        scraper = config["class"](
            base_url=getattr(args, "base_url", None) or "",
            urls=getattr(args, "urls", None),
            output_dir=output_dir,
            force=args.force,
        )
    elif config.get("requires_api_type"):
        scraper = config["class"](
            api_type=config["api_type"],
            output_dir=output_dir,
            force=args.force,
        )
    else:
        scraper = config["class"](output_dir=output_dir, force=args.force)

    # Run the scraper
    scraper.run()


if __name__ == "__main__":
    main()

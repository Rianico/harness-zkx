#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "rich>=13.0.0",
# ]
# ///
"""Rust documentation scraper using cargo-docs-md.

This scraper generates LLM-friendly markdown from Rust crate documentation
by leveraging the cargo-docs-md tool, which converts rustdoc JSON to markdown.

STABILITY NOTE:
  The markdown output from cargo-docs-md is experimental. The tool's output
  format, directory structure, and link conventions may change between versions.
  The flattening and link-rewriting logic in this scraper is tightly coupled to
  the output format of cargo-docs-md v0.2.x. If you upgrade cargo-docs-md,
  re-run the verification pipeline (flatten -> rewrite -> verify) and check for
  broken links before using the output in production.

VERSION COMPATIBILITY (tested as of 2025-05):
  Rust nightly toolchain: required (rustdoc JSON output is nightly-only)
  cargo-docs-md:          v0.2.4
  rustc:                  1.88.0+
  rustdoc JSON format:    v29 (corresponds to nightly-2025-05+)

  The rustdoc JSON format version is not stable across Rust releases. If the
  nightly toolchain is updated and cargo-docs-md fails, pin the nightly
  toolchain to a known-working date:
    rustup toolchain install nightly-2025-05-01

Prerequisites:
  - Rust nightly toolchain: rustup toolchain install nightly
  - cargo-docs-md: cargo install cargo-docs-md --locked

Workflow:
  1. Clone the crate source (if not local)
  2. Generate rustdoc JSON using nightly
  3. Convert to markdown using cargo-docs-md
  4. Filter to target crates only (optional, for workspaces)
  5. Flatten module/index.md -> module.md (compact output)
  6. Rewrite internal links for the flattened structure
  7. Verify all internal links resolve
"""

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Markdown link pattern shared by _rewrite_links and _verify_links
MD_LINK_PATTERN = re.compile(r'\]\(([^)]+\.md[^)]*)\)')


def _get_crate_dirs(output_dir: Path) -> set[str]:
    """Return names of top-level crate directories."""
    return {item.name for item in output_dir.iterdir() if item.is_dir()}


def _split_link(link: str) -> tuple[str, str] | None:
    """Split a markdown link into (path, anchor). Returns None for external URLs."""
    if link.startswith(('http://', 'https://')):
        return None
    if '#' in link:
        path, anchor = link.split('#', 1)
        return path, f'#{anchor}'
    return link, ''


@dataclass
class LinkContext:
    """Per-file context for link rewriting, computed once before processing links."""
    md_file: Path
    was_flattened: bool
    is_crate_child: bool
    crate_dirs: set[str]
    file_set: set[Path]
    dir_set: set[Path]

    def path_exists(self, path: Path) -> bool:
        return path.resolve() in self.file_set

    def dir_exists(self, path: Path) -> bool:
        return path.resolve() in self.dir_set

    def try_rewrite(self, candidate: str, anchor: str) -> str | None:
        """If candidate path resolves, return formatted markdown link; else None."""
        if self.path_exists(self.md_file.parent / candidate):
            return f']({candidate}{anchor})'
        return None


def _strip_leading_dotdot(path: str) -> str:
    """Remove one leading ../ from a path."""
    return path[3:] if path.startswith('../') else path


def _fix_flatten_index(ctx: LinkContext, link_path: str, anchor: str) -> str | None:
    """Fix 1: Convert /index.md -> .md with depth adjustment."""
    if '/index.md' not in link_path:
        return None

    new_path = link_path.replace('/index.md', '.md')
    if ctx.was_flattened and new_path.startswith('../'):
        new_path = _strip_leading_dotdot(new_path)
        if not new_path.startswith(('./', '../')):
            new_path = './' + new_path
    elif ctx.is_crate_child and new_path.startswith('../'):
        bare = _strip_leading_dotdot(new_path)
        if bare.replace('.md', '') not in ctx.crate_dirs:
            new_path = './' + bare

    result = ctx.try_rewrite(new_path, anchor)
    if result:
        return result

    # Submodule directory prefix (e.g., from symbols.md: bar.md -> ./symbols/bar.md)
    module_name = ctx.md_file.stem
    module_dir = ctx.md_file.parent / module_name
    if ctx.dir_exists(module_dir):
        candidate = f'./{module_name}/{new_path}' if not new_path.startswith('./') else f'./{module_name}/{new_path[2:]}'
        result = ctx.try_rewrite(candidate, anchor)
        if result:
            return result

    # Fallback: /index.md -> .md without depth change
    alt_path = link_path.replace('/index.md', '.md')
    return ctx.try_rewrite(alt_path, anchor)


def _fix_reduce_depth(ctx: LinkContext, link_path: str, anchor: str) -> str | None:
    """Fix 2: Reduce ../ count for flattened/crate-child files."""
    dotdot_count = link_path.count('../')
    remainder = link_path.replace('../', '')

    needs_reduction = (ctx.was_flattened and dotdot_count >= 1) or (ctx.is_crate_child and dotdot_count >= 2)
    if not needs_reduction:
        return None

    reduced = '../' * (dotdot_count - 1) + remainder
    if not reduced.startswith(('./', '../')):
        reduced = './' + reduced
    return ctx.try_rewrite(reduced, anchor)


def _fix_parent_module(ctx: LinkContext, link_path: str, anchor: str) -> str | None:
    """Fix 3: ../index.md -> ../parentname.md when parent was flattened."""
    if not link_path.endswith('index.md'):
        return None

    dotdot_count = link_path.count('../')
    current = ctx.md_file.parent
    for _ in range(dotdot_count):
        current = current.parent

    dir_name = current.name
    if not dir_name or not ctx.path_exists(current.parent / f'{dir_name}.md'):
        return None

    if dotdot_count <= 1:
        new_path = f'./{dir_name}.md'
    else:
        new_path = f'{"../" * max(0, dotdot_count - 1)}{dir_name}.md'
    return ctx.try_rewrite(new_path, anchor)


def _fix_subdir_lookup(ctx: LinkContext, link_path: str, anchor: str) -> str | None:
    """Fix 4: Bare filename.md or module/index.md -> ./module/filename.md."""
    has_slash = '/' in link_path
    is_module_index = link_path.count('/') == 1 and link_path.endswith('/index.md')
    if has_slash and not is_module_index:
        return None

    module_name = ctx.md_file.stem
    module_dir = ctx.md_file.parent / module_name
    lookup_name = link_path.replace('/index.md', '.md') if '/index.md' in link_path else link_path
    if ctx.dir_exists(module_dir) and ctx.path_exists(module_dir / lookup_name):
        return f'](./{module_name}/{lookup_name}{anchor})'
    return None


def _fix_parent_index(ctx: LinkContext, link_path: str, anchor: str) -> str | None:
    """Fix 4c+4d: index.md or ../index.md -> ../parentname.md."""
    if link_path not in ('index.md', '../index.md'):
        return None
    # index.md from flattened/crate-child already handled by self-reference check
    if link_path == 'index.md' and (ctx.was_flattened or ctx.is_crate_child):
        return None

    parent_name = ctx.md_file.parent.name
    parent_md = ctx.md_file.parent.parent / f'{parent_name}.md'
    if ctx.path_exists(parent_md):
        return f'](../{parent_name}.md{anchor})'
    return None


def _fix_sibling(ctx: LinkContext, link_path: str, anchor: str) -> str | None:
    """Fix 5+6: ../module.md or ../dir/file.md -> ./module.md or ./dir/file.md for crate children."""
    if not ctx.is_crate_child or not link_path.startswith('../'):
        return None

    parts_after = _strip_leading_dotdot(link_path)

    # Fix 5: ../module.md (sibling file)
    if '/' not in parts_after:
        bare_name = parts_after.replace('.md', '')
        if bare_name not in ctx.crate_dirs and ctx.path_exists(ctx.md_file.parent / parts_after):
            return f'](./{parts_after}{anchor})'
        return None

    # Fix 6: ../dir/file.md (sibling directory)
    dir_name = parts_after.split('/')[0]
    if dir_name not in ctx.crate_dirs:
        return ctx.try_rewrite('./' + parts_after, anchor)
    return None


# Strategy execution order matters — each is tried in sequence until one matches
_LINK_FIX_STRATEGIES = [
    _fix_flatten_index,
    _fix_reduce_depth,
    _fix_parent_module,
    _fix_subdir_lookup,
    _fix_parent_index,
    _fix_sibling,
]



RUST_URL_PATTERNS = [
    r"^https?://docs\.rs/[^/]+",  # docs.rs/crate_name
    r"^https?://crates\.io/crates/[^/]+",  # crates.io/crates/crate_name
    r"^https?://github\.com/[^/]+/[^/]+(?:\.git)?$",  # GitHub repos (may be Rust)
    r"^https?://gitlab\.com/[^/]+/[^/]+(?:\.git)?$",  # GitLab repos (may be Rust)
]

# Known Rust TUI/framework crates for auto-detection
KNOWN_RUST_CRATES = {
    "ratatui", "tui-rs", "crossterm", "termion", "termwiz",
    "tokio", "async-std", "actix", "warp", "axum",
    "serde", "clap", "anyhow", "thiserror",
    "bevy", "egui", "iced", "druid",
}


def detect_rust_project(url: str | None = None, path: Path | None = None) -> tuple[bool, str]:
    """Detect if target is a Rust project.

    Args:
        url: URL to check (docs.rs, crates.io, GitHub, etc.)
        path: Local path to check for Cargo.toml

    Returns:
        Tuple of (is_rust, reason) where reason explains the detection
    """
    if path:
        cargo_toml = path / "Cargo.toml"
        if cargo_toml.exists():
            return True, f"Found Cargo.toml at {path}"

    if url:
        # Check docs.rs pattern
        docs_match = re.match(r"^https?://docs\.rs/([^/]+)", url)
        if docs_match:
            crate_name = docs_match.group(1)
            return True, f"docs.rs URL indicates Rust crate: {crate_name}"

        # Check crates.io pattern
        crates_match = re.match(r"^https?://crates\.io/crates/([^/]+)", url)
        if crates_match:
            crate_name = crates_match.group(1)
            return True, f"crates.io URL indicates Rust crate: {crate_name}"

        # Check GitHub/GitLab with known Rust crate name
        for pattern in [r"github\.com/[^/]+/([^/]+)", r"gitlab\.com/[^/]+/([^/]+)"]:
            match = re.search(pattern, url)
            if match:
                repo_name = match.group(1).replace("-", "_").lower()
                if repo_name in KNOWN_RUST_CRATES:
                    return True, f"Known Rust crate repository: {match.group(1)}"

    return False, "Not detected as Rust project"


def check_prerequisites() -> tuple[bool, str]:
    """Check if required tools are installed.

    Returns:
        Tuple of (success, error_message)
    """
    # Check cargo-docs-md
    result = subprocess.run(
        ["cargo", "docs-md", "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, (
            "cargo-docs-md not installed. Install with:\n"
            "  cargo install cargo-docs-md --locked"
        )

    # Check nightly toolchain
    result = subprocess.run(
        ["rustup", "run", "nightly", "rustc", "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, (
            "Rust nightly toolchain not installed. Install with:\n"
            "  rustup toolchain install nightly"
        )

    return True, ""


class RustScraper:
    """Scrapes Rust crate documentation using cargo-docs-md."""

    name = "rust"
    description = """Generate markdown documentation from Rust crate source.

    Uses cargo-docs-md to convert rustdoc JSON to LLM-friendly markdown.
    Requires Rust nightly and cargo-docs-md to be installed.

    Input can be:
      - A crate name from crates.io (e.g., 'ratatui')
      - A GitHub repository URL (e.g., 'https://github.com/ratatui/ratatui')
      - A local path to a Rust project

    Examples:
      scrape.py rust ratatui --output-dir ./docs/ratatui
      scrape.py rust https://github.com/ratatui/ratatui --output-dir ./docs
      scrape.py rust ./my-crate --output-dir ./docs
    """

    def __init__(
        self,
        target: str,
        output_dir: Path,
        force: bool = False,
        primary_crate: str | None = None,
        include_deps: bool = False,
        include_examples: bool = False,
        full_method_docs: bool = True,
        exclude_private: bool = True,
    ):
        """Initialize the Rust scraper.

        Args:
            target: Crate name, GitHub URL, or local path
            output_dir: Directory to write markdown output
            force: Re-clone and regenerate even if cached
            primary_crate: For workspaces, the main crate to prioritize
            include_deps: Include dependency documentation (default: only workspace crates)
            include_examples: Include example crates from workspace (default: False)
            full_method_docs: Include full method documentation
            exclude_private: Exclude private items from output
        """
        self.target = target
        self.output_dir = output_dir
        self.force = force
        self.primary_crate = primary_crate
        self.include_deps = include_deps
        self.include_examples = include_examples
        self.full_method_docs = full_method_docs
        self.exclude_private = exclude_private

        self.temp_dir: Path | None = None
        self.source_dir: Path | None = None
        self.json_dir: Path | None = None

    def _resolve_target(self) -> Path:
        """Resolve target to a local path with Rust source code.

        Returns:
            Path to the Rust project directory
        """
        target = self.target

        # Check if it's a local path
        local_path = Path(target)
        if local_path.exists() and (local_path / "Cargo.toml").exists():
            console.print(f"[green]Using local path:[/] {local_path}")
            return local_path

        # Check if it's a GitHub URL
        if target.startswith(("https://github.com/", "https://gitlab.com/")):
            return self._clone_repository(target)

        # Check if it's a docs.rs URL
        if target.startswith("https://docs.rs/"):
            # Extract crate name
            parts = target.split("/")
            if len(parts) >= 5:
                crate_name = parts[4]
                repo_url = f"https://github.com/{crate_name}-org/{crate_name}"
                console.print(f"[yellow]Attempting to clone from:[/] {repo_url}")
                return self._clone_repository(repo_url)

        # Assume it's a crate name - try to find GitHub repo
        if re.match(r"^[a-zA-Z0-9_-]+$", target):
            # Try common GitHub patterns
            possible_urls = [
                f"https://github.com/{target}-org/{target}",
                f"https://github.com/{target}/{target}",
                f"https://github.com/ratatui-org/{target}",  # Special case for ratatui ecosystem
            ]
            for url in possible_urls:
                try:
                    result = subprocess.run(
                        ["git", "ls-remote", url],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        console.print(f"[green]Found repository at:[/] {url}")
                        return self._clone_repository(url)
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    continue

            raise ValueError(
                f"Could not find GitHub repository for crate '{target}'. "
                f"Please provide the full repository URL."
            )

        raise ValueError(
            f"Could not resolve target: {target}\n"
            f"Expected: crate name, GitHub URL, or local path to Rust project"
        )

    def _clone_repository(self, url: str) -> Path:
        """Clone a git repository to a temporary directory.

        Args:
            url: Git repository URL

        Returns:
            Path to cloned repository
        """
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rust-scraper-"))
        self.source_dir = self.temp_dir / "source"

        console.print(f"[cyan]Cloning repository:[/] {url}")

        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(self.source_dir)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone repository: {result.stderr}")

        return self.source_dir

    def _detect_primary_crate(self, source_dir: Path) -> str | None:
        """Detect the primary crate in a workspace.

        Args:
            source_dir: Path to Rust project

        Returns:
            Primary crate name or None
        """
        cargo_toml = source_dir / "Cargo.toml"

        # Check if it's a workspace
        content = cargo_toml.read_text()
        if "[workspace]" not in content:
            # Single crate - get name from Cargo.toml
            match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
            if match:
                return match.group(1)
            return None

        # Workspace - try to find the main crate
        # Common patterns: same name as directory, or 'main' member
        dir_name = source_dir.name.lower().replace("-", "_")

        # Check workspace members
        members_match = re.search(r"members\s*=\s*\[([^\]]+)\]", content)
        if members_match:
            members_str = members_match.group(1)
            members = re.findall(r'"([^"]+)"', members_str)

            # Check if directory name matches a member
            for member in members:
                member_name = member.strip("/").replace("-", "_")
                if member_name == dir_name:
                    return member_name

            # Return first non-example member
            for member in members:
                if "example" not in member.lower():
                    return member.strip("/").replace("-", "_")

        return None

    def _generate_rustdoc_json(self, source_dir: Path) -> Path:
        """Generate rustdoc JSON for the project.

        Args:
            source_dir: Path to Rust project

        Returns:
            Path to directory containing JSON files
        """
        json_dir = source_dir / "target" / "doc"
        json_dir.mkdir(parents=True, exist_ok=True)

        console.print("[cyan]Generating rustdoc JSON (requires nightly)...[/]")
        console.print("[dim]This may take a while for large projects...[/]")

        # Build command - always build all to get workspace members
        # We filter to workspace crates afterwards
        cmd = [
            "cargo", "+nightly", "doc",
        ]

        # Set environment for unstable JSON output
        env = os.environ.copy()
        env["RUSTDOCFLAGS"] = "-Z unstable-options --output-format json"

        result = subprocess.run(
            cmd,
            cwd=source_dir,
            capture_output=True,
            text=True,
            env=env,
        )

        if result.returncode != 0:
            # Check if it's a toolchain issue
            if "requires rustc" in result.stderr:
                raise RuntimeError(
                    f"Rust version mismatch. Update nightly:\n"
                    f"  rustup update nightly\n\n"
                    f"Error: {result.stderr}"
                )
            raise RuntimeError(f"Failed to generate rustdoc JSON: {result.stderr}")

        return json_dir

    def _filter_json_files(self, json_dir: Path, primary_crate: str | None) -> Path | None:
        """Filter to only target crate JSON files.

        This reduces output from all dependencies to just the workspace crates.

        Args:
            json_dir: Directory containing all JSON files
            primary_crate: Primary crate name for filtering

        Returns:
            Path to filtered JSON directory, or None if filtering not needed
        """
        import glob as glob_module

        all_jsons = list(json_dir.glob("*.json"))
        if not all_jsons:
            return None

        # Find workspace crate JSONs (those matching crate names in the source)
        # Track which crates are examples (in examples/ directories)
        workspace_crates = set()
        example_crates = set()

        # Check for workspace members
        source_dir = json_dir.parent.parent  # target/doc -> target -> source
        cargo_toml = source_dir / "Cargo.toml"

        if cargo_toml.exists():
            content = cargo_toml.read_text()
            # Find all crate names in root
            names = re.findall(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
            workspace_crates.update(names)

            # Check workspace members
            members_match = re.search(r"members\s*=\s*\[([^\]]+)\]", content)
            if members_match:
                members_str = members_match.group(1)
                members = re.findall(r'"([^"]+)"', members_str)
                for member in members:
                    # Check if this is an examples directory
                    is_example = "example" in member.lower()

                    # Handle glob patterns like 'ratatui-*' or 'examples/*'
                    if '*' in member:
                        # Use glob to expand pattern
                        pattern = str(source_dir / member / "Cargo.toml")
                        for member_cargo in glob_module.glob(pattern):
                            member_cargo_path = Path(member_cargo)
                            if member_cargo_path.exists():
                                # Check if path contains 'examples'
                                is_example_path = "examples" in member_cargo_path.parts
                                member_content = member_cargo_path.read_text()
                                member_names = re.findall(r'^name\s*=\s*"([^"]+)"', member_content, re.MULTILINE)
                                for name in member_names:
                                    workspace_crates.add(name)
                                    if is_example or is_example_path:
                                        example_crates.add(name)
                    else:
                        # Explicit path
                        member_path = source_dir / member.strip("/")
                        member_cargo = member_path / "Cargo.toml"
                        if member_cargo.exists():
                            member_content = member_cargo.read_text()
                            member_names = re.findall(r'^name\s*=\s*"([^"]+)"', member_content, re.MULTILINE)
                            workspace_crates.update(member_names)
                            if is_example:
                                example_crates.update(member_names)

        if not workspace_crates:
            return None

        # Create filtered directory
        self.json_dir = Path(tempfile.mkdtemp(prefix="rust-json-"))

        included_count = 0
        for crate in sorted(workspace_crates):
            # Skip examples unless include_examples is True
            if crate in example_crates and not self.include_examples:
                continue

            # Crate names in Cargo.toml use hyphens, but JSON files use underscores
            json_name = crate.replace("-", "_")
            json_file = json_dir / f"{json_name}.json"
            if json_file.exists():
                dest = self.json_dir / json_file.name
                dest.write_bytes(json_file.read_bytes())
                console.print(f"  [dim]Including crate:[/] {crate}")
                included_count += 1

        if included_count == 0:
            console.print("[yellow]Warning:[/] No workspace crates found after filtering")
            return None

        if not list(self.json_dir.glob("*.json")):
            return None

        return self.json_dir

    def _generate_markdown(self, json_dir: Path, output_dir: Path) -> None:
        """Generate markdown from rustdoc JSON.

        Args:
            json_dir: Directory containing JSON files
            output_dir: Output directory for markdown
        """
        console.print("[cyan]Generating markdown with cargo-docs-md...[/]")

        cmd = [
            "cargo", "docs-md",
            "--dir", str(json_dir),
            "--output", str(output_dir),
        ]

        if self.primary_crate:
            cmd.extend(["--primary-crate", self.primary_crate])

        if self.exclude_private:
            cmd.append("--exclude-private")

        if self.full_method_docs:
            cmd.append("--full-method-docs")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to generate markdown: {result.stderr}")

        # Print output info
        if result.stdout:
            console.print(result.stdout)

    def _cleanup_markdown(self, output_dir: Path) -> None:
        """Remove meaningless elements from generated markdown.

        COUPLING NOTE: The cleanup patterns are specific to artifacts produced
        by cargo-docs-md v0.2.x (empty anchor spans, empty divs). If the tool
        changes its HTML generation, these patterns may need updating.

        Args:
            output_dir: Directory containing markdown files
        """
        md_files = list(output_dir.glob("**/*.md"))
        if not md_files:
            return

        console.print("[dim]Cleaning up markdown artifacts...[/]")

        # Patterns for meaningless elements
        patterns = [
            # Empty anchor spans: <span id="foo"></span>
            (r'<span id="[^"]+"></span>\n?', ""),
            # Empty div elements: <div id="foo"></div>
            (r'<div id="[^"]+"></div>\n?', ""),
            # Multiple consecutive blank lines (reduce to max 2)
            (r'\n{3,}', "\n\n"),
        ]

        cleaned_count = 0
        for md_file in md_files:
            content = md_file.read_text()
            original_len = len(content)

            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)

            if len(content) != original_len:
                md_file.write_text(content)
                cleaned_count += 1

        if cleaned_count > 0:
            console.print(f"[dim]Cleaned {cleaned_count} files[/]")

    def _flatten_structure(self, output_dir: Path) -> set[str]:
        """Flatten subdirectory structure from module/index.md to module.md.

        This ONLY flattens subdirectories within crates, NOT the crate roots themselves.
        Crate roots stay as `crate/index.md` to preserve cross-crate link paths.

        COUPLING NOTE: This logic depends on cargo-docs-md v0.2.x output format,
        which generates `module/index.md` for each Rust module. If cargo-docs-md
        changes its output structure (e.g., flat files by default), this method
        and _rewrite_links will need to be updated or removed.

        Returns:
            Set of flattened module paths (relative to output_dir) for link rewriting.
        """
        console.print("[dim]Flattening subdirectory structure...[/]")

        flattened_count = 0
        files_to_move = []
        flattened_modules: set[str] = set()

        crate_dirs = _get_crate_dirs(output_dir)

        # Collect all files to move
        for index_file in list(output_dir.glob("**/index.md")):
            parent_dir = index_file.parent

            # Skip the root index.md (if any)
            if parent_dir == output_dir:
                continue

            # Skip crate roots (top-level crate directories with index.md)
            if parent_dir.parent == output_dir:
                continue

            # Only flatten subdirectories within crates
            flattened_path = parent_dir.parent / f"{parent_dir.name}.md"
            files_to_move.append((index_file, flattened_path, parent_dir))

        # Move files
        for index_file, flattened_path, parent_dir in files_to_move:
            if flattened_path.exists():
                console.print(f"[yellow]Skipping:[/] {index_file} (target exists: {flattened_path.name})")
                continue

            # Track this flattened module
            original_rel = index_file.relative_to(output_dir)
            flattened_modules.add(str(original_rel.parent))  # e.g., "ratatui_core/style/palette"

            index_file.rename(flattened_path)
            flattened_count += 1

        # Remove empty directories
        removed_dirs = 0
        for index_file, flattened_path, parent_dir in files_to_move:
            try:
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    removed_dirs += 1
            except OSError:
                pass

        if flattened_count > 0:
            console.print(f"[dim]Flattened {flattened_count} files, removed {removed_dirs} empty directories[/]")

        return flattened_modules

    def _rewrite_links(self, output_dir: Path, flattened_modules: set[str]) -> None:
        """Rewrite links for the flattened subdirectory structure.

        After flattening module/index.md -> module.md, every file that was at
        depth N within a crate is now at depth N-1. Links that used ../ to go
        up to parent modules need one fewer ../, and links to flattened modules
        need /index.md replaced with .md.

        COUPLING NOTE: The fix strategies are empirical — derived from observing
        broken-link patterns in cargo-docs-md v0.2.x output after flattening.
        See _LINK_FIX_STRATEGIES for the ordered list of strategy functions.

        Args:
            output_dir: Directory containing markdown files
            flattened_modules: Set of module paths that were flattened (e.g., "ratatui_core/style/palette")
        """
        console.print("[dim]Rewriting internal links...[/]")

        md_files = list(output_dir.glob("**/*.md"))
        if not md_files:
            return

        rewritten_count = 0
        crate_dirs = _get_crate_dirs(output_dir)

        # Pre-build existence sets to avoid repeated filesystem stat calls
        file_set = {p.resolve() for p in output_dir.glob("**/*") if p.is_file()}
        dir_set = {p.resolve() for p in output_dir.glob("**/*") if p.is_dir()}

        for md_file in md_files:
            content = md_file.read_text()
            original_content = content

            file_rel = md_file.relative_to(output_dir)
            file_parts = file_rel.parts

            containing_crate = file_parts[0] if len(file_parts) > 1 and file_parts[0] in crate_dirs else None
            is_crate_root = md_file.name == 'index.md' and containing_crate and len(file_parts) == 2
            is_summary = md_file.name == 'SUMMARY.md' and md_file.parent == output_dir

            file_parent = str(file_rel.parent)
            file_stem = md_file.stem
            was_flattened = f"{file_parent}/{file_stem}" in flattened_modules if file_parent != '.' else file_stem in flattened_modules
            is_crate_child = containing_crate is not None and len(file_parts) == 2 and md_file.name != 'index.md'

            ctx = LinkContext(
                md_file=md_file,
                was_flattened=was_flattened,
                is_crate_child=is_crate_child,
                crate_dirs=crate_dirs,
                file_set=file_set,
                dir_set=dir_set,
            )

            def rewrite_link(match: re.Match) -> str:
                link = match.group(1)

                split = _split_link(link)
                if split is None:
                    return match.group(0)

                link_path, anchor = split
                if not link_path.endswith('.md'):
                    return match.group(0)

                # Self-reference: for flattened files, bare index.md -> #
                if link_path == 'index.md' and ctx.was_flattened:
                    return f']({anchor})' if anchor else '](#)'

                # If link resolves as-is, no fix needed
                if ctx.path_exists(ctx.md_file.parent / link_path):
                    return match.group(0)

                # Try each strategy in order
                for strategy in _LINK_FIX_STRATEGIES:
                    result = strategy(ctx, link_path, anchor)
                    if result is not None:
                        return result

                return match.group(0)

            content = MD_LINK_PATTERN.sub(rewrite_link, content)

            # Fix SUMMARY.md crate links
            if is_summary:
                for crate_name in crate_dirs:
                    pattern = rf'\]\({crate_name}\.md(\#[^)]*)?\)'
                    replacement = rf']({crate_name}/index.md\1)'
                    content = re.sub(pattern, replacement, content)

            # Fix crate root cross-crate links
            if is_crate_root:
                for crate_name in crate_dirs:
                    if crate_name != md_file.parent.name:
                        pattern = rf'\]\(\.\./{crate_name}\.md(\#[^)]*)?\)'
                        replacement = rf'](../{crate_name}/index.md\1)'
                        content = re.sub(pattern, replacement, content)

            if content != original_content:
                md_file.write_text(content)
                rewritten_count += 1

        if rewritten_count > 0:
            console.print(f"[dim]Rewrote links in {rewritten_count} files[/]")

    def _verify_links(self, output_dir: Path, file_set: set[Path] | None = None) -> list[tuple[Path, str]]:
        """Verify all internal links resolve correctly."""
        console.print("[dim]Verifying internal links...[/]")

        md_files = list(output_dir.glob("**/*.md"))
        if not md_files:
            return []

        if file_set is None:
            file_set = {p.resolve() for p in output_dir.glob("**/*") if p.is_file()}

        broken_links = []

        for md_file in md_files:
            content = md_file.read_text()

            for match in MD_LINK_PATTERN.finditer(content):
                link = match.group(1)

                split = _split_link(link)
                if split is None:
                    continue

                link_path, _ = split
                if link_path in ('CONTRIBUTING.md', '../CONTRIBUTING.md', '../../CONTRIBUTING.md'):
                    continue

                target_path = (md_file.parent / link_path).resolve()

                if target_path not in file_set:
                    broken_links.append((md_file, link))

        if broken_links:
            console.print(f"[yellow]Warning:[/] Found {len(broken_links)} broken links:")
            for md_file, link in broken_links[:10]:
                console.print(f"  {md_file.relative_to(output_dir)}: {link}")
            if len(broken_links) > 10:
                console.print(f"  ... and {len(broken_links) - 10} more")
        else:
            console.print("[green]All internal links verified[/]")

        return broken_links

    def _cleanup(self) -> None:
        """Clean up temporary directories."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        if self.json_dir and self.json_dir.exists():
            shutil.rmtree(self.json_dir, ignore_errors=True)

    def _generate_readme(
        self,
        output_dir: Path,
        crate_name: str,
        source_url: str | None = None,
        version: str | None = None,
        extra_metadata: dict[str, str] | None = None,
    ) -> None:
        """Generate a README.md with documentation metadata.

        Args:
            output_dir: Directory to write README.md
            crate_name: Name of the Rust crate
            source_url: URL where crate was sourced (GitHub, docs.rs, etc.)
            version: Crate version if available
            extra_metadata: Additional key-value pairs to include
        """
        readme_path = output_dir / "README.md"

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        date_display = now.strftime("%Y-%m-%d %H:%M UTC")

        lines = [
            f"# {crate_name} Documentation",
            "",
            f"**Scraped:** {date_display}",
            "",
            "## Source",
            "",
        ]

        if source_url:
            lines.append(f"- **URL:** {source_url}")
        else:
            lines.append(f"- **Crate:** {crate_name}")

        if version:
            lines.append(f"- **Version:** {version}")

        if extra_metadata:
            for key, value in extra_metadata.items():
                lines.append(f"- **{key}:** {value}")

        lines.extend([
            "",
            "## Usage",
            "",
            "This documentation was generated from Rust crate source code using `cargo-docs-md`. ",
            "The content is optimized for AI assistant consumption with:",
            "",
            "- Clean markdown formatting",
            "- Module structure preserved",
            "- Cross-crate links resolved",
            "",
            "### Caveats",
            "",
            "- **Freshness:** This snapshot was taken on a specific date. Check crates.io or GitHub for updates.",
            "- **Accuracy:** Some formatting may differ from docs.rs. Refer to official docs for canonical content.",
            "- **Generated:** This documentation is auto-generated. The original doc comments are in the source code.",
        ])

        if source_url:
            lines.extend([
                "",
                "### Version Check",
                "",
                f"To get the latest version, check [crates.io](https://crates.io/crates/{crate_name}) ",
                f"or the [source repository]({source_url}).",
            ])

        lines.extend([
            "",
            "---",
            f"*Generated by scraper skill on {date_str}*",
        ])

        readme_path.write_text("\n".join(lines), encoding="utf-8")
        console.print(f"[green]Generated:[/] {readme_path}")

    def run(self) -> None:
        """Execute the Rust documentation scraping workflow."""
        try:
            # Check prerequisites
            ok, error = check_prerequisites()
            if not ok:
                console.print(f"[red]Error:[/] {error}")
                return

            # Resolve target to source path
            source_dir = self._resolve_target()

            # Detect primary crate if not specified
            if not self.primary_crate:
                self.primary_crate = self._detect_primary_crate(source_dir)
                if self.primary_crate:
                    console.print(f"[dim]Detected primary crate:[/] {self.primary_crate}")

            # Generate rustdoc JSON
            json_dir = self._generate_rustdoc_json(source_dir)

            # Filter to workspace crates only (unless include_deps)
            if not self.include_deps:
                filtered_dir = self._filter_json_files(json_dir, self.primary_crate)
                if filtered_dir:
                    json_dir = filtered_dir

            # Generate markdown
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self._generate_markdown(json_dir, self.output_dir)

            # Flatten directory structure (module/index.md -> module.md)
            flattened_modules = self._flatten_structure(self.output_dir)

            # Rewrite internal links to match new structure
            self._rewrite_links(self.output_dir, flattened_modules)

            # Cleanup markdown artifacts
            self._cleanup_markdown(self.output_dir)

            # Verify all links work (reuse file_set from rewrite step)
            file_set = {p.resolve() for p in self.output_dir.glob("**/*") if p.is_file()}
            broken_links = self._verify_links(self.output_dir, file_set)

            # Report results
            md_files = list(self.output_dir.glob("**/*.md"))
            console.print(f"\n[green]Success![/] Generated {len(md_files)} markdown files")
            console.print(f"[green]Output directory:[/] {self.output_dir}")

            # Generate README with metadata
            crate_name = self.primary_crate or self.target
            # Determine source URL
            source_url = None
            if self.target.startswith(("https://", "http://")):
                source_url = self.target
            elif self.source_dir and self.source_dir.exists():
                # Try to get git remote URL
                try:
                    result = subprocess.run(
                        ["git", "remote", "get-url", "origin"],
                        cwd=self.source_dir,
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        source_url = result.stdout.strip()
                except Exception:
                    pass

            # Try to get version from Cargo.toml
            version = None
            if self.source_dir:
                cargo_toml = self.source_dir / "Cargo.toml"
                if cargo_toml.exists():
                    content = cargo_toml.read_text()
                    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
                    if match:
                        version = match.group(1)

            self._generate_readme(
                output_dir=self.output_dir,
                crate_name=crate_name,
                source_url=source_url,
                version=version,
                extra_metadata={
                    "Files": str(len(md_files)),
                    "Include Dependencies": "Yes" if self.include_deps else "No (workspace only)",
                },
            )

            # Show structure
            console.print(f"\n[dim]Structure:[/]")
            for item in sorted(self.output_dir.iterdir())[:10]:
                if item.is_dir():
                    count = len(list(item.glob("**/*.md")))
                    console.print(f"  {item.name}/ ({count} files)")
                else:
                    console.print(f"  {item.name}")
            if len(list(self.output_dir.iterdir())) > 10:
                console.print("  ...")

        except Exception as e:
            console.print(f"[red]Error:[/] {e}")
            raise
        finally:
            self._cleanup()


def main() -> None:
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Rust documentation scraper")
    parser.add_argument("target", help="Crate name, GitHub URL, or local path")
    parser.add_argument("--output-dir", type=Path, default=Path("./rust-docs"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--primary-crate", help="Primary crate for workspaces")
    parser.add_argument("--include-deps", action="store_true", help="Include dependencies")
    parser.add_argument("--full-method-docs", action="store_true", default=True)
    parser.add_argument("--exclude-private", action="store_true", default=True)

    args = parser.parse_args()

    scraper = RustScraper(
        target=args.target,
        output_dir=args.output_dir,
        force=args.force,
        primary_crate=args.primary_crate,
        include_deps=args.include_deps,
        full_method_docs=args.full_method_docs,
        exclude_private=args.exclude_private,
    )
    scraper.run()


if __name__ == "__main__":
    main()

"""Asset integrity verification for md-to-html.

Verifies that files in assets/ match their expected SHA-256 hashes.
Assets are immutable third-party files — they must never be manually edited.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
SKILL_DIR = SCRIPT_DIR.parent
ASSETS_DIR = SKILL_DIR / "assets"
MANIFEST_PATH = ASSETS_DIR / "MANIFEST.json"


def compute_hash(path: Path) -> str:
    """Compute SHA-256 hex digest of *path*."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict:
    """Load the manifest file. Returns empty dict if missing."""
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {}


def save_manifest(manifest: dict) -> None:
    """Write *manifest* to disk."""
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")


def build_manifest() -> dict:
    """Scan assets/ and build a fresh manifest with hashes and metadata."""
    manifest: dict = {}
    for f in sorted(ASSETS_DIR.iterdir()):
        if f.name == "MANIFEST.json" or f.is_dir():
            continue
        entry = manifest.get(f.name, {})
        entry["sha256"] = compute_hash(f)
        if "source" not in entry:
            entry["source"] = "unknown"
        if "version" not in entry:
            entry["version"] = "unknown"
        manifest[f.name] = entry
    return manifest


def verify() -> bool:
    """Verify all asset files match their expected hashes.

    Returns True when all files pass.
    """
    manifest = load_manifest()
    if not manifest:
        print("ERROR: No MANIFEST.json found in assets/. Run with --update first.")
        return False

    all_ok = True
    expected_files = set(manifest.keys())
    actual_files = {
        f.name for f in ASSETS_DIR.iterdir() if f.is_file() and f.name != "MANIFEST.json"
    }

    for name in sorted(expected_files - actual_files):
        print(f"MISSING: {name} (in manifest but not on disk)")
        all_ok = False

    for name in sorted(actual_files - expected_files):
        print(f"UNTRACKED: {name} (on disk but not in manifest)")
        all_ok = False

    for name in sorted(expected_files & actual_files):
        expected = manifest[name]["sha256"]
        actual = compute_hash(ASSETS_DIR / name)
        if actual != expected:
            print(f"MISMATCH: {name}")
            print(f"  expected: {expected}")
            print(f"  actual:   {actual}")
            all_ok = False

    if all_ok:
        print("OK: All assets verified.")
    return all_ok


def update() -> None:
    """Regenerate manifest from current asset files, preserving metadata."""
    old = load_manifest()
    manifest = build_manifest()
    for name, entry in manifest.items():
        if name in old:
            entry["source"] = old[name].get("source", "unknown")
            entry["version"] = old[name].get("version", "unknown")
    save_manifest(manifest)
    print(f"Updated: {MANIFEST_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify md-to-html asset integrity")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Regenerate MANIFEST.json from current asset files",
    )
    args = parser.parse_args()

    if args.update:
        update()
    else:
        ok = verify()
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()

# /// script
# dependencies = []
# ///
"""
Configuration loading for the observation hook.
"""

from __future__ import annotations

from pathlib import Path


def get_homunculus_dir() -> Path:
    """Get the homunculus data directory path."""
    home = Path.home()
    return home / ".claude" / "lsz" / "homunculus"


def get_config_path() -> Path:
    """Get the path to the user config.properties file."""
    return get_homunculus_dir() / "config.properties"


def get_default_config_path() -> Path:
    """Get the path to the bundled default config.properties.

    Returns path to skills/continuous-learning/scripts/config.properties.
    """
    # Navigate from hooks/observe/ to project root, then to scripts/
    project_root = Path(__file__).parent.parent.parent
    return project_root / "skills" / "continuous-learning" / "scripts" / "config.properties"


def ensure_user_config(homunculus_dir: Path) -> Path:
    """Ensure user config exists, copying from bundled default if needed.

    Args:
        homunculus_dir: Path to homunculus data directory.

    Returns:
        Path to user config file (created or existing).
    """
    config_path = homunculus_dir / "config.properties"
    if not config_path.exists():
        homunculus_dir.mkdir(parents=True, exist_ok=True)
        default_path = get_default_config_path()
        if default_path.exists():
            config_path.write_text(default_path.read_text())
    return config_path


def load_config() -> dict[str, str | int]:
    """
    Load configuration from config.properties.

    Priority:
    1. User override at ~/.claude/lsz/homunculus/config.properties
    2. Bundled default at skills/continuous-learning/scripts/config.properties
    3. Hardcoded defaults
    """
    defaults = {
        "signal_every_n": 20,
        "min_observations_to_analyze": 50,
        "run_interval_minutes": 5,
        "retention_days": 30,
        "max_file_size_mb": 10,
        "observer_model": "haiku",
    }

    # Check user override first, then bundled default
    config_path = get_config_path()
    if not config_path.exists():
        config_path = get_default_config_path()
    if not config_path.exists():
        return defaults

    config = dict(defaults)
    with open(config_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key in defaults:
                    # Try to convert to int if default is int
                    if isinstance(defaults[key], int):
                        try:
                            config[key] = int(value)
                        except ValueError:
                            config[key] = value
                    else:
                        config[key] = value

    return config


def get_signal_interval() -> int:
    """Get the number of observations before signaling daemon."""
    config = load_config()
    return int(config.get("signal_every_n", 20))

"""
Timezone utilities for consistent time handling across the project.

Auto-detects local timezone from the host machine.
Uses ISO 8601 compact format for display (e.g., +0800).
"""

import platform
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def _detect_tz_macos() -> str | None:
    """Detect timezone on macOS."""
    # Method 1: systemsetup command
    try:
        result = subprocess.run(
            ["systemsetup", "-gettimezone"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            # Output: "Time Zone: Asia/Shanghai"
            line = result.stdout.strip()
            if ":" in line:
                tz = line.split(":", 1)[1].strip()
                if tz:
                    return tz
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Method 2: /etc/localtime symlink
    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        # Symlink points to something like /var/db/timezone/zoneinfo/Asia/Shanghai
        target = str(localtime.resolve())
        if "zoneinfo" in target:
            # Extract the timezone name after zoneinfo/
            parts = target.split("zoneinfo")
            if len(parts) > 1:
                return parts[1].lstrip("/")

    return None


def _detect_tz_linux() -> str | None:
    """Detect timezone on Linux."""
    # Method 1: /etc/timezone file (Debian/Ubuntu)
    tz_file = Path("/etc/timezone")
    if tz_file.exists():
        return tz_file.read_text().strip()

    # Method 2: /etc/localtime symlink
    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        # Symlink points to /usr/share/zoneinfo/Asia/Shanghai
        target = str(localtime.resolve())
        if "zoneinfo" in target:
            parts = target.split("zoneinfo")
            if len(parts) > 1:
                return parts[1].lstrip("/")

    return None


def _detect_local_tz_name() -> str:
    """Detect local timezone name from the system."""
    system = platform.system()

    if system == "Darwin":
        tz_name = _detect_tz_macos()
    elif system == "Linux":
        tz_name = _detect_tz_linux()
    else:
        tz_name = None

    return tz_name or "UTC"


def get_local_tz() -> ZoneInfo:
    """Get the local timezone from the host machine."""
    tz_name = _detect_local_tz_name()
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("UTC")


# Module-level cache for local timezone
_LOCAL_TZ: ZoneInfo | None = None


def local_tz() -> ZoneInfo:
    """Get cached local timezone."""
    global _LOCAL_TZ
    if _LOCAL_TZ is None:
        _LOCAL_TZ = get_local_tz()
    return _LOCAL_TZ


def now_local() -> datetime:
    """Get current time in local timezone."""
    return datetime.now(local_tz())


def now_local_iso() -> str:
    """Get current time in local timezone as ISO 8601 string."""
    return now_local().isoformat()


def now_local_compact() -> str:
    """Get current time in local timezone with compact offset for storage."""
    dt = now_local()
    return dt.isoformat()  # Full ISO 8601 with microseconds and offset


def to_local_display(utc_ts: str) -> str:
    """
    Convert UTC timestamp to local timezone for display.

    Args:
        utc_ts: UTC timestamp string (ISO 8601 with Z or +00:00 suffix)

    Returns:
        Local time string with compact offset (e.g., '2026-05-02 20:00 +0800')
    """
    if not utc_ts:
        return utc_ts
    try:
        # Parse the timestamp
        if utc_ts.endswith("Z"):
            dt = datetime.fromisoformat(utc_ts.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(utc_ts)

        # Convert to local timezone
        local_dt = dt.astimezone(local_tz())
        offset = local_dt.strftime("%z")
        return local_dt.strftime("%Y-%m-%d %H:%M") + " " + offset
    except (ValueError, TypeError):
        return utc_ts


# Backwards compatibility aliases (CST = Asia/Shanghai)
# These are deprecated; use local_tz() instead
TZ_CST = ZoneInfo("Asia/Shanghai")


def now_cst() -> datetime:
    """Deprecated: Use now_local() instead."""
    return datetime.now(TZ_CST)


def now_cst_iso() -> str:
    """Deprecated: Use now_local_iso() instead."""
    return datetime.now(TZ_CST).isoformat()


def now_cst_compact() -> str:
    """Deprecated: Use now_local_iso() instead."""
    return datetime.now(TZ_CST).isoformat()

"""
Sentinel integration API for host applications (e.g. Mimic).

Import this module to run Sentinel checks from within a host:
    from sentinel.api import run_quick_check, run_full_sweep, get_available_drives, sweep_due, ...
"""

from datetime import datetime

from sentinel.config import load_config, save_config
from sentinel.core import quick_check
from sentinel.drive import get_available_drives, get_drive_usage
from sentinel.recommendation import recommend_schedule, get_quality_warnings
from sentinel.sweep import full_sweep, sweep_due, read_last_sweep_timestamp


def run_quick_check(
    drive: str,
    size_fraction: float | None = None,
    progress_callback=None,
    abort_check=None,
) -> dict:
    """
    Run a quick integrity check on the given drive.
    Host can pass progress_callback(current, total, message) and abort_check() for cancellation.
    Returns dict with passed, message, details, verification_details; if aborted, also aborted=True, etc.
    """
    if size_fraction is None:
        from sentinel.recommendation import recommend_check_size_fraction
        size_fraction = recommend_check_size_fraction(drive)
    return quick_check(drive, size_fraction, progress_callback, abort_check)


def run_full_sweep(
    drive: str,
    progress_callback=None,
    abort_check=None,
) -> dict:
    """
    Run full sweep (manifest verify + free-space) on the given drive.
    Returns dict with passed, message, details, manifest_passed, free_space_passed, verification_details.
    """
    return full_sweep(
        drive,
        progress_callback=progress_callback,
        manifest_callback=progress_callback,  # phase transitions
        abort_check=abort_check,
    )


def is_sweep_due(drive: str, interval_days: int | None = None) -> bool:
    """Return True if full sweep is due for the drive based on interval."""
    if interval_days is None:
        config = load_config()
        interval_days = config.get("sweep_interval_days", 14)
    return sweep_due(drive, interval_days)


def get_last_check_time() -> datetime | None:
    """Return last quick check timestamp from config, or None."""
    config = load_config()
    s = config.get("last_check_time")
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def get_last_sweep_time(drive: str | None = None) -> datetime | None:
    """
    Return last full sweep timestamp. Prefers on-card timestamp if drive given;
    otherwise uses config fallback.
    """
    if drive:
        ts = read_last_sweep_timestamp(drive)
        if ts:
            return ts
    config = load_config()
    s = config.get("last_sweep_time")
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def get_recommendation(drive: str) -> tuple[int, str]:
    """Return (recommended_interval_days, hint_str) for the drive."""
    return recommend_schedule(drive)


def get_warnings(drive: str) -> list[str]:
    """Return quality/size warnings for the drive (e.g. very small, nearly full)."""
    return get_quality_warnings(drive)

"""Config load/save for Sentinel."""

import json
import os
from pathlib import Path


_CONFIG_DIR_NAME = "Sentinel"
_CONFIG_FILE_NAME = "sentinel_config.json"
_DEFAULT_SIZE_FRACTION = 0.10
_DEFAULT_SWEEP_INTERVAL_DAYS = 14


def _get_config_path() -> Path:
    """Return the path to the config file in user data directory."""
    if hasattr(Path, "home"):
        base = Path.home()
    else:
        base = Path(os.environ.get("APPDATA", "."))
    config_dir = base / _CONFIG_DIR_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / _CONFIG_FILE_NAME


def load_config() -> dict:
    """
    Load config from JSON file.
    Returns dict with keys: last_drive, check_size_fraction, sweep_interval_days,
    last_check_time (iso str or None), last_sweep_time (iso str or None, fallback when not on card).
    """
    config_path = _get_config_path()
    if not config_path.exists():
        return {
            "last_drive": None,
            "check_size_fraction": _DEFAULT_SIZE_FRACTION,
            "sweep_interval_days": _DEFAULT_SWEEP_INTERVAL_DAYS,
            "last_check_time": None,
            "last_sweep_time": None,
        }
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
        return {
            "last_drive": data.get("last_drive"),
            "check_size_fraction": data.get("check_size_fraction", _DEFAULT_SIZE_FRACTION),
            "sweep_interval_days": data.get("sweep_interval_days", _DEFAULT_SWEEP_INTERVAL_DAYS),
            "last_check_time": data.get("last_check_time"),
            "last_sweep_time": data.get("last_sweep_time"),
        }
    except (json.JSONDecodeError, OSError):
        return {
            "last_drive": None,
            "check_size_fraction": _DEFAULT_SIZE_FRACTION,
            "sweep_interval_days": _DEFAULT_SWEEP_INTERVAL_DAYS,
            "last_check_time": None,
            "last_sweep_time": None,
        }


def save_config(
    last_drive: str | None = None,
    check_size_fraction: float | None = None,
    sweep_interval_days: int | None = None,
    last_check_time: str | None = None,
    last_sweep_time: str | None = None,
) -> None:
    """
    Save config to JSON file.
    Pass only the keys to update; others are preserved.
    """
    config_path = _get_config_path()
    current = load_config()
    if last_drive is not None:
        current["last_drive"] = last_drive
    if check_size_fraction is not None:
        current["check_size_fraction"] = check_size_fraction
    if sweep_interval_days is not None:
        current["sweep_interval_days"] = sweep_interval_days
    if last_check_time is not None:
        current["last_check_time"] = last_check_time
    if last_sweep_time is not None:
        current["last_sweep_time"] = last_sweep_time
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)

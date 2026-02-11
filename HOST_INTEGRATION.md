# Sentinel Host Integration Guide

This document describes how to integrate Sentinel with a host application (e.g. Mimic) so users can run SD card checks from within the host.

## Integration Options

### 1. Import as Python module (recommended)

If your host is Python, add the Sentinel project directory to `sys.path` and import:

```python
from sentinel.api import (
    run_quick_check,
    run_full_sweep,
    get_available_drives,
    is_sweep_due,
    get_last_check_time,
    get_last_sweep_time,
    get_recommendation,
    get_warnings,
)
```

**API functions:**

| Function | Returns | Description |
|----------|---------|-------------|
| `run_quick_check(drive, size_fraction=None, progress_callback=None, abort_check=None)` | `dict` | Run quick check. Returns `passed`, `message`, `details`, `verification_details`. Use `abort_check=lambda: should_stop` for cancellation. |
| `run_full_sweep(drive, progress_callback=None, abort_check=None)` | `dict` | Run full sweep. Returns `passed`, `message`, `manifest_passed`, `free_space_passed`, etc. |
| `get_available_drives()` | `list[str]` | List drive roots, e.g. `["C:\\", "G:\\"]`. |
| `is_sweep_due(drive, interval_days=None)` | `bool` | True if full sweep is due based on last sweep time. |
| `get_last_check_time()` | `datetime \| None` | Last quick check timestamp from config. |
| `get_last_sweep_time(drive=None)` | `datetime \| None` | Last full sweep timestamp (prefers on-card if drive given). |
| `get_recommendation(drive)` | `(int, str)` | `(recommended_interval_days, hint_str)`. |
| `get_warnings(drive)` | `list[str]` | Quality warnings, e.g. "Card very small (< 4 GB)". |

**Shared config:** Sentinel stores `last_check_time`, `last_sweep_time`, `last_drive`, `sweep_interval_days` in the user's config directory. Host and Sentinel share this automatically when using the API.

### 2. Subprocess (CLI)

For non-Python hosts or when you prefer process isolation:

```bash
# Quick check on G:
python -m sentinel check G:\

# Full sweep on G:
python -m sentinel sweep G:\

# List drives (JSON):
python -m sentinel drives

# Launch standalone UI:
python -m sentinel ui
```

**Note:** Run from the `sentinel-phase2` project directory, or ensure it is on `PYTHONPATH`.

Exit codes: `0` = passed, `1` = failed or error. Output is JSON for `check` and `sweep`.

### 3. Host-side integration checklist

- **Menu item:** Add "Run Sentinel check" or "Check SD card health" to host menu. Call `run_quick_check(drive)` or spawn `python -m sentinel check <drive>`.
- **On-launch prompt:** When host launches, if an SD/card drive is detected and `is_sweep_due(drive, interval)` is True, prompt: "Run Sentinel check now?"
- **Banner/indicator:** Optional "Sentinel standing vigil" indicator when integrated.

### 4. Standalone mode

Sentinel remains fully runnable standalone (`python sentinel_ui.py` or `python -m sentinel ui`). Integration is additive.

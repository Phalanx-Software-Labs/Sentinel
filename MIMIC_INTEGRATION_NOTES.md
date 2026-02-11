# Mimic Integration Notes (Phase 4)

When integrating Sentinel with Mimic, the Mimic project should implement:

## 1. Menu item

- Add menu: "Run Sentinel check" or "Check SD card health"
- On click: call `run_quick_check(drive)` (Python) or spawn `python -m sentinel check <drive>` (subprocess)
- Use the SD card drive that Mimic uses for game storage

## 2. On-launch prompt (optional)

- When Mimic launches, if an SD card is detected:
  - Call `is_sweep_due(drive, interval_days)` (or check `get_last_check_time()` vs. interval)
  - If due, show prompt: "Run Sentinel check now?" (Yes / No / Later)
  - If Yes, run `run_quick_check(drive)` (or full sweep if preferred)

## 3. Banner / indicator (optional)

- Show "Sentinel standing vigil" or similar when integrated, to indicate SD health checking is available

## 4. Sentinel API location

- Import path: `from sentinel.api import run_quick_check, ...`
- Ensure `sentinel-phase2` (or Sentinel install path) is on `sys.path`, or add it before import

## 5. Shared config

- Sentinel stores last check/sweep times in user config. Mimic does not need to manage this; Sentinel handles it when `run_quick_check` or `run_full_sweep` completes.

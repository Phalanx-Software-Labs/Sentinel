"""
CLI entry point for Sentinel. Allows host apps to invoke Sentinel via subprocess.

Usage:
    python -m sentinel check G:\\          # Run quick check on G:
    python -m sentinel sweep G:\\          # Run full sweep on G:
    python -m sentinel ui                  # Launch standalone UI
    python -m sentinel drives              # List available drives (JSON)
"""

import json
import sys


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python -m sentinel {check|sweep|ui|drives} [drive]")
        sys.exit(1)
    cmd = args[0].lower()
    drive = args[1] if len(args) > 1 else None
    if not drive and cmd in ("check", "sweep"):
        from sentinel.drive import get_available_drives
        drives = get_available_drives()
        drive = drives[0] if drives else None
        if not drive:
            print("No drives found.")
            sys.exit(1)
    if cmd == "check":
        from sentinel.api import run_quick_check
        result = run_quick_check(drive)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("passed", False) else 1)
    elif cmd == "sweep":
        from sentinel.api import run_full_sweep
        result = run_full_sweep(drive)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("passed", False) else 1)
    elif cmd == "ui":
        from sentinel_ui import main as ui_main
        ui_main()
    elif cmd == "drives":
        from sentinel.drive import get_available_drives
        drives = get_available_drives()
        print(json.dumps(drives))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()

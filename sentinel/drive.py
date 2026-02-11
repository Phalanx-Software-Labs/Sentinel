"""Drive enumeration and disk usage for Sentinel."""

import shutil
from pathlib import Path


def get_available_drives() -> list[str]:
    """
    Return a list of available Windows drive roots (e.g. ["C:\\", "G:\\"]).
    Iterates A–Z and checks Path(f"{d}:\\").exists().
    """
    drives = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        root = Path(f"{letter}:\\")
        if root.exists():
            drives.append(str(root))
    return drives


def get_drive_usage(path: str) -> tuple[int, int]:
    """
    Return (total_bytes, free_bytes) for the given path.
    Uses shutil.disk_usage.
    """
    usage = shutil.disk_usage(path)
    return usage.total, usage.free

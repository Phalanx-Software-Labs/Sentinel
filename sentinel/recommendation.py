"""Schedule recommendation and quality hints for Sentinel Phase 3."""

from sentinel.drive import get_drive_usage

# Capacity thresholds (bytes)
VERY_SMALL_BYTES = 4 * 1024 * 1024 * 1024  # 4 GB
SMALL_BYTES = 32 * 1024 * 1024 * 1024  # 32 GB
BALANCED_BYTES = 128 * 1024 * 1024 * 1024  # 128 GB
HIGH_END_BYTES = 256 * 1024 * 1024 * 1024  # 256 GB

# Usage threshold for "nearly full" warning
FULL_THRESHOLD = 0.95  # 95%


def recommend_schedule(drive_root: str) -> tuple[int, str]:
    """
    Recommend sweep interval based on drive capacity.
    Returns (interval_days, hint_str).
    Low-end/small: 7 days. Balanced: 14 days. High-end: 21–30 days.
    """
    total, _ = get_drive_usage(drive_root)
    if total < SMALL_BYTES:
        return 7, "Low-end / small card (recommend checking every 7 days)"
    if total < BALANCED_BYTES:
        return 14, "Balanced capacity (recommend checking every 14 days)"
    if total < HIGH_END_BYTES:
        return 21, "High-capacity card (recommend checking every 21 days)"
    return 30, "High-capacity card (recommend checking every 30 days)"


def get_quality_warnings(drive_root: str) -> list[str]:
    """
    Return list of warnings for small or nearly full cards.
    E.g. "Card very small (< 4 GB)", "Card nearly full (> 95%)"
    """
    warnings = []
    total, free = get_drive_usage(drive_root)
    used = total - free
    if total > 0:
        used_pct = used / total
        if total < VERY_SMALL_BYTES:
            warnings.append("Card very small (< 4 GB)")
        if used_pct >= FULL_THRESHOLD:
            pct = int(used_pct * 100)
            warnings.append(f"Card nearly full ({pct}% used)")
    return warnings


def recommend_check_size_fraction(drive_root: str) -> float:
    """
    Recommend quick check size fraction based on capacity.
    Small cards: 5%. Normal: 10%.
    """
    total, _ = get_drive_usage(drive_root)
    if total < SMALL_BYTES:
        return 0.05
    return 0.10

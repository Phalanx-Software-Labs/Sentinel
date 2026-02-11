"""Integrity check logic for Sentinel."""

import hashlib
import os
import random
import secrets
from datetime import datetime
from pathlib import Path

from sentinel.drive import get_drive_usage

SAFETY_MARGIN_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB cap (FAT32 limit 4GB; avoids large-write issues)
WRITE_CHUNK_BYTES = 64 * 1024 * 1024  # 64 MB per write chunk
TEMP_DIR_PREFIX = "SentinelCheck"


def quick_check(
    drive_root: str,
    size_fraction: float = 0.10,
    progress_callback=None,
    abort_check=None,
) -> dict:
    """
    Run a quick integrity check on the given drive.

    Writes test files in batches (each batch capped at 2GB, written in 64MB chunks),
    total size = size_fraction of drive. Each batch: write → verify (read 2×) → pass/fail
    before the next. Deletes all test data before returning.

    Args:
        drive_root: Path to drive root (e.g. "C:\\" or "G:\\").
        size_fraction: Fraction of drive to test (default 0.10 = 10%).
        progress_callback: Optional callable(current, total, message) for progress.
        abort_check: Optional callable() -> bool; if True, stop and return partial result.

    Returns:
        dict with passed, message, details, verification_details; if aborted, also
        aborted=True, batches_completed, batches_total, bytes_tested, bytes_total,
        extrapolated_confidence_pct.
    """
    total_bytes_d, free_bytes_d = get_drive_usage(drive_root)
    target_bytes = int(size_fraction * total_bytes_d)
    usable_bytes = max(0, free_bytes_d - SAFETY_MARGIN_BYTES)
    size_bytes = min(target_bytes, usable_bytes)

    if size_bytes < 1024:
        return {
            "passed": False,
            "message": "Integrity check failed",
            "details": "Not enough free space for check (need at least 100 MB free).",
            "verification_details": [],
        }

    # Split into batches; each batch (file) <= 2GB
    batch_sizes = []
    remaining = size_bytes
    while remaining > 0:
        batch_sizes.append(min(remaining, MAX_FILE_BYTES))
        remaining -= batch_sizes[-1]
    num_batches = len(batch_sizes)
    total_steps = num_batches * 3  # write, verify1, verify2 per batch

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_random = secrets.token_hex(4)
    temp_dir_name = f"{TEMP_DIR_PREFIX}_{date_str}_{short_random}"
    temp_path = Path(drive_root) / temp_dir_name

    try:
        temp_path.mkdir(parents=True, exist_ok=False)
    except OSError as e:
        return {
            "passed": False,
            "message": "Integrity check failed",
            "details": f"Could not create test directory: {e}",
            "verification_details": [],
        }

    verification_details = []
    aborted = False

    try:
        for batch_i, fsize in enumerate(batch_sizes):
            if abort_check and abort_check():
                aborted = True
                break

            file_path = temp_path / f"test_{batch_i}.bin"

            # Write batch in 64MB chunks
            if progress_callback:
                progress_callback(
                    batch_i * 3,
                    total_steps,
                    f"Writing batch {batch_i + 1}/{num_batches}…",
                )
            hasher = hashlib.sha256()
            rng = random.Random(batch_i)
            try:
                with open(file_path, "wb") as f:
                    written = 0
                    while written < fsize:
                        chunk_size = min(WRITE_CHUNK_BYTES, fsize - written)
                        chunk = rng.randbytes(chunk_size)
                        hasher.update(chunk)
                        f.write(chunk)
                        written += chunk_size
            except OSError as e:
                return {
                    "passed": False,
                    "message": "Integrity check failed",
                    "details": f"Write error (batch {batch_i + 1}): {e}",
                    "verification_details": verification_details,
                }
            expected_hash = hasher.hexdigest()

            # Verify read 1
            if progress_callback:
                progress_callback(
                    batch_i * 3 + 1,
                    total_steps,
                    f"Verifying batch {batch_i + 1}/{num_batches} (read 1)…",
                )
            try:
                h1 = _hash_file_chunked(file_path, WRITE_CHUNK_BYTES)
            except OSError as e:
                return {
                    "passed": False,
                    "message": "Integrity check failed",
                    "details": f"Read error (batch {batch_i + 1}): {e}",
                    "verification_details": verification_details,
                }
            if h1 != expected_hash:
                verification_details.append({
                    "batch": batch_i + 1,
                    "expected_hash": expected_hash,
                    "read1_hash": h1,
                    "read2_hash": None,
                    "match": False,
                })
                return {
                    "passed": False,
                    "message": "Integrity check failed",
                    "details": f"Hash mismatch on batch {batch_i + 1} (first read).",
                    "verification_details": verification_details,
                }

            # Verify read 2
            if progress_callback:
                progress_callback(
                    batch_i * 3 + 2,
                    total_steps,
                    f"Verifying batch {batch_i + 1}/{num_batches} (read 2)…",
                )
            try:
                h2 = _hash_file_chunked(file_path, WRITE_CHUNK_BYTES)
            except OSError as e:
                return {
                    "passed": False,
                    "message": "Integrity check failed",
                    "details": f"Read error (batch {batch_i + 1}, second pass): {e}",
                    "verification_details": verification_details,
                }
            match = h1 == expected_hash and h2 == expected_hash and h1 == h2
            verification_details.append({
                "batch": batch_i + 1,
                "expected_hash": expected_hash,
                "read1_hash": h1,
                "read2_hash": h2,
                "match": match,
            })
            if not match:
                return {
                    "passed": False,
                    "message": "Integrity check failed",
                    "details": f"Hash mismatch on batch {batch_i + 1} (second read).",
                    "verification_details": verification_details,
                }

        if aborted:
            batches_completed = len(verification_details)
            bytes_tested = sum(batch_sizes[i] for i in range(batches_completed))
            total_batches = num_batches
            confidence_pct = round(100 * bytes_tested / size_bytes) if size_bytes else 0
            return {
                "passed": all(v.get("match", False) for v in verification_details),
                "message": "Check aborted by user",
                "details": (
                    f"{batches_completed}/{total_batches} batches completed, "
                    f"all passed. {bytes_tested:,} of {size_bytes:,} bytes tested (~{confidence_pct}%). "
                    f"Extrapolated: no failures in tested area."
                ),
                "verification_details": verification_details,
                "aborted": True,
                "batches_completed": batches_completed,
                "batches_total": total_batches,
                "bytes_tested": bytes_tested,
                "bytes_total": size_bytes,
                "extrapolated_confidence_pct": confidence_pct,
            }
        if progress_callback:
            progress_callback(total_steps, total_steps, "Cleaning up…")
        return {
            "passed": True,
            "message": "Integrity check passed",
            "details": f"Verified {num_batches} batches, {size_bytes:,} bytes total.",
            "verification_details": verification_details,
        }

    finally:
        try:
            for f in temp_path.iterdir():
                f.unlink()
            temp_path.rmdir()
        except OSError:
            pass


def _hash_file_chunked(path: Path, chunk_size: int) -> str:
    """Read file in chunks and return SHA-256 hex digest."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

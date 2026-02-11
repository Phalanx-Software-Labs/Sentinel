"""Full sweep logic for Sentinel Phase 2."""

import hashlib
import json
import os
import random
import secrets
from datetime import datetime
from pathlib import Path

from sentinel.config import _get_config_path
from sentinel.core import (
    MAX_FILE_BYTES,
    SAFETY_MARGIN_BYTES,
    WRITE_CHUNK_BYTES,
    _hash_file_chunked,
)
from sentinel.drive import get_drive_usage

SENTINEL_DIR = "Sentinel"
LAST_SWEEP_FILE = ".last_sweep"
TEMP_DIR_PREFIX = "SentinelSweep"


def _manifest_path(drive_root: str) -> Path:
    """Path to manifest file on PC (per drive)."""
    base = _get_config_path().parent
    letter = drive_root.replace("\\", "").replace(":", "").upper() or "UNKNOWN"
    base = base / "manifests"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{letter}.json"


def _sentinel_path(drive_root: str) -> Path:
    """Path to Sentinel folder on card."""
    return Path(drive_root) / SENTINEL_DIR


def read_last_sweep_timestamp(drive_root: str) -> datetime | None:
    """Read last full sweep timestamp from card. Returns None if not found or invalid."""
    path = _sentinel_path(drive_root) / LAST_SWEEP_FILE
    if not path.exists():
        return None
    try:
        s = path.read_text(encoding="utf-8").strip()
        return datetime.fromisoformat(s)
    except (ValueError, OSError):
        return None


def write_last_sweep_timestamp(drive_root: str) -> None:
    """Write current timestamp to card (Sentinel/.last_sweep)."""
    sentinel_dir = _sentinel_path(drive_root)
    sentinel_dir.mkdir(parents=True, exist_ok=True)
    path = sentinel_dir / LAST_SWEEP_FILE
    path.write_text(datetime.now().isoformat(), encoding="utf-8")


def sweep_due(drive_root: str, interval_days: int) -> bool:
    """True if full sweep is due (no timestamp or >= interval_days since last)."""
    last = read_last_sweep_timestamp(drive_root)
    if last is None:
        return True
    delta = datetime.now() - last
    return delta.days >= interval_days


def build_manifest(
    drive_root: str, progress_callback=None, abort_check=None
) -> tuple[dict[str, str], list[str], bool]:
    """
    Build manifest of all files on drive (path -> hash). Skips Sentinel dir.
    Returns (manifest_dict, list of paths hashed, aborted).
    """
    root = Path(drive_root)
    manifest = {}
    paths = []
    sentinel_abs = _sentinel_path(drive_root)

    all_files = []
    for p in root.rglob("*"):
        if p.is_file() and not str(p).startswith(str(sentinel_abs)):
            all_files.append(p)
    total = len(all_files)

    for i, p in enumerate(all_files):
        if abort_check and abort_check():
            return manifest, paths, True
        if progress_callback:
            progress_callback(i, max(total, 1), f"Building manifest: {p.name[:40]}…")
        try:
            h = _hash_file_chunked(p, WRITE_CHUNK_BYTES)
            rel = str(p.relative_to(root)).replace("\\", "/")
            manifest[rel] = h
            paths.append(rel)
        except OSError:
            pass  # skip unreadable files
    return manifest, paths, False


def save_manifest(drive_root: str, manifest: dict[str, str]) -> None:
    """Save manifest to PC."""
    path = _manifest_path(drive_root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_manifest(drive_root: str) -> dict[str, str] | None:
    """Load manifest from PC. Returns None if not found."""
    path = _manifest_path(drive_root)
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def verify_manifest(
    drive_root: str,
    manifest: dict[str, str],
    progress_callback=None,
    abort_check=None,
) -> tuple[bool, list[str], list[dict], bool]:
    """
    Re-read and re-hash all files in manifest; compare.
    Returns (passed, list of mismatches, verification_details, aborted).
    """
    root = Path(drive_root)
    mismatches = []
    verification_details = []
    entries = list(manifest.items())
    total = max(len(entries), 1)

    for i, (rel, expected_hash) in enumerate(entries):
        if abort_check and abort_check():
            return len(mismatches) == 0, mismatches, verification_details, True
        if progress_callback:
            progress_callback(i, total, f"Verifying files: {rel[:40]}…")
        path = root / rel.replace("/", os.sep)
        if not path.exists():
            mismatches.append(f"{rel} (missing)")
            verification_details.append({
                "path": rel,
                "expected_hash": expected_hash,
                "read_hash": None,
                "match": False,
                "note": "missing",
            })
            continue
        try:
            h = _hash_file_chunked(path, WRITE_CHUNK_BYTES)
            match = h == expected_hash
            verification_details.append({
                "path": rel,
                "expected_hash": expected_hash,
                "read_hash": h,
                "match": match,
                "note": None,
            })
            if not match:
                mismatches.append(rel)
        except OSError:
            mismatches.append(f"{rel} (read error)")
            verification_details.append({
                "path": rel,
                "expected_hash": expected_hash,
                "read_hash": None,
                "match": False,
                "note": "read error",
            })

    return len(mismatches) == 0, mismatches, verification_details, False


def free_space_sweep(
    drive_root: str, progress_callback=None, abort_check=None
) -> dict:
    """
    Write/verify/delete over all free space (minus safety margin). Same pattern as quick_check.
    Returns dict with passed, message, details.
    """
    total_bytes_d, free_bytes_d = get_drive_usage(drive_root)
    usable_bytes = max(0, free_bytes_d - SAFETY_MARGIN_BYTES)

    if usable_bytes < 1024:
        return {
            "passed": False,
            "message": "Free-space sweep failed",
            "details": "Not enough free space (need at least 100 MB free).",
            "verification_details": [],
        }

    verification_details = []
    batch_sizes = []
    remaining = usable_bytes
    while remaining > 0:
        batch_sizes.append(min(remaining, MAX_FILE_BYTES))
        remaining -= batch_sizes[-1]
    num_batches = len(batch_sizes)
    total_steps = num_batches * 3

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_random = secrets.token_hex(4)
    temp_dir_name = f"{TEMP_DIR_PREFIX}_{date_str}_{short_random}"
    temp_path = Path(drive_root) / temp_dir_name

    try:
        temp_path.mkdir(parents=True, exist_ok=False)
    except OSError as e:
        return {
            "passed": False,
            "message": "Free-space sweep failed",
            "details": f"Could not create test directory: {e}",
            "verification_details": [],
        }

    try:
        for batch_i, fsize in enumerate(batch_sizes):
            if abort_check and abort_check():
                batches_done = len(verification_details)
                bytes_tested = sum(batch_sizes[i] for i in range(batches_done))
                confidence_pct = round(100 * bytes_tested / usable_bytes) if usable_bytes else 0
                return {
                    "passed": all(v.get("match", False) for v in verification_details),
                    "message": "Free-space sweep aborted by user",
                    "details": (
                        f"{batches_done}/{num_batches} batches completed, all passed. "
                        f"{bytes_tested:,} of {usable_bytes:,} bytes (~{confidence_pct}%). "
                        f"Extrapolated: no failures in tested area."
                    ),
                    "verification_details": verification_details,
                    "aborted": True,
                    "batches_completed": batches_done,
                    "batches_total": num_batches,
                    "bytes_tested": bytes_tested,
                    "bytes_total": usable_bytes,
                    "extrapolated_confidence_pct": confidence_pct,
                }
            file_path = temp_path / f"test_{batch_i}.bin"
            if progress_callback:
                progress_callback(
                    batch_i * 3,
                    total_steps,
                    f"Free space: writing batch {batch_i + 1}/{num_batches}…",
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
                    "message": "Free-space sweep failed",
                    "details": f"Write error (batch {batch_i + 1}): {e}",
                    "verification_details": verification_details,
                }
            expected_hash = hasher.hexdigest()

            if progress_callback:
                progress_callback(
                    batch_i * 3 + 1,
                    total_steps,
                    f"Free space: verifying batch {batch_i + 1}/{num_batches} (read 1)…",
                )
            try:
                h1 = _hash_file_chunked(file_path, WRITE_CHUNK_BYTES)
            except OSError as e:
                return {
                    "passed": False,
                    "message": "Free-space sweep failed",
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
                    "message": "Free-space sweep failed",
                    "details": f"Hash mismatch on batch {batch_i + 1} (first read).",
                    "verification_details": verification_details,
                }

            if progress_callback:
                progress_callback(
                    batch_i * 3 + 2,
                    total_steps,
                    f"Free space: verifying batch {batch_i + 1}/{num_batches} (read 2)…",
                )
            try:
                h2 = _hash_file_chunked(file_path, WRITE_CHUNK_BYTES)
            except OSError as e:
                return {
                    "passed": False,
                    "message": "Free-space sweep failed",
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
                    "message": "Free-space sweep failed",
                    "details": f"Hash mismatch on batch {batch_i + 1} (second read).",
                    "verification_details": verification_details,
                }

        if progress_callback:
            progress_callback(total_steps, total_steps, "Cleaning up…")
        return {
            "passed": True,
            "message": "Free-space sweep passed",
            "details": f"Verified {num_batches} batches, {usable_bytes:,} bytes total.",
            "verification_details": verification_details,
        }
    finally:
        try:
            for f in temp_path.iterdir():
                f.unlink()
            temp_path.rmdir()
        except OSError:
            pass


def full_sweep(
    drive_root: str,
    progress_callback=None,
    manifest_callback=None,
    abort_check=None,
) -> dict:
    """
    Run full sweep: build or load manifest, verify files, free-space sweep, write timestamp.
    progress_callback(current, total, message) for progress.
    manifest_callback(phase) called at phase transitions for UI (e.g. "manifest", "verify", "free_space").
    abort_check: optional callable() -> bool; if True, stop and return partial result (no timestamp written).
    Returns dict with passed, message, details, manifest_passed, free_space_passed; if aborted, also aborted=True.
    """
    result = {
        "passed": True,
        "message": "Full sweep passed",
        "details": "",
        "manifest_passed": True,
        "free_space_passed": True,
        "verification_details": {"manifest": [], "free_space": []},
    }
    parts = []

    # 1. Manifest: build or load
    manifest = load_manifest(drive_root)
    if manifest is None:
        if manifest_callback:
            manifest_callback("build_manifest")
        m, paths, build_aborted = build_manifest(
            drive_root, progress_callback, abort_check
        )
        if build_aborted:
            result["aborted"] = True
            result["message"] = "Full sweep aborted"
            result["details"] = (
                f"Manifest build aborted. {len(paths)} files hashed. "
                "No manifest saved; no timestamp written."
            )
            result["verification_details"]["manifest"] = []
            return result
        save_manifest(drive_root, m)
        manifest = m
        parts.append("Manifest built (new card).")
    else:
        # 2. Verify manifest
        if manifest_callback:
            manifest_callback("verify_manifest")
        passed, mismatches, manifest_vd, verify_aborted = verify_manifest(
            drive_root, manifest, progress_callback, abort_check
        )
        result["manifest_passed"] = passed
        result["verification_details"]["manifest"] = manifest_vd
        if verify_aborted:
            result["aborted"] = True
            result["message"] = "Full sweep aborted"
            verified_count = sum(1 for v in manifest_vd if v.get("match"))
            total_verified = len(manifest_vd)
            result["details"] = (
                f"File verification aborted. {verified_count}/{total_verified} files verified, "
                f"all matched. No timestamp written."
            )
            return result
        if not passed:
            result["passed"] = False
            result["message"] = "Full sweep failed"
            parts.append(f"File verification failed ({len(mismatches)} mismatch(es)): " + "; ".join(mismatches[:5]))
            if len(mismatches) > 5:
                parts[-1] += f" … and {len(mismatches) - 5} more"
            result["details"] = "\n".join(parts)
            return result
        parts.append("File verification passed.")

    # 3. Free-space sweep
    if manifest_callback:
        manifest_callback("free_space")
    fs_result = free_space_sweep(drive_root, progress_callback, abort_check)
    result["free_space_passed"] = fs_result.get("passed", False)
    result["verification_details"]["free_space"] = fs_result.get(
        "verification_details", []
    )
    if fs_result.get("aborted"):
        result["aborted"] = True
        result["message"] = "Full sweep aborted"
        result["details"] = "\n".join(parts) + "\n" + fs_result.get("details", "")
        return result
    if not result["free_space_passed"]:
        result["passed"] = False
        result["message"] = "Full sweep failed"
        parts.append(f"Free-space sweep failed: {fs_result.get('details', '')}")
        result["details"] = "\n".join(parts)
        return result
    parts.append(fs_result.get("details", ""))

    # 4. Write timestamp (only when not aborted)
    write_last_sweep_timestamp(drive_root)

    result["details"] = "\n".join(parts)
    return result

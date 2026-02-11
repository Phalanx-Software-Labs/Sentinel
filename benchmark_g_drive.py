"""Benchmark G: drive write speed. Writes test data, times it, reports MB/s."""

import os
import random
import sys
import time
from pathlib import Path

DRIVE = "G:\\"
CHUNK_MB = 64
TOTAL_MB = 128  # 128 MB per test
TEMP_FILE_URANDOM = "SentinelBenchmark_urandom.bin"
TEMP_FILE_FAST = "SentinelBenchmark_fast.bin"


def benchmark_write(use_urandom: bool):
    path = Path(DRIVE) / (TEMP_FILE_URANDOM if use_urandom else TEMP_FILE_FAST)
    total_bytes = TOTAL_MB * 1024 * 1024
    chunk_bytes = CHUNK_MB * 1024 * 1024
    rng = random.Random(42) if not use_urandom else None

    print(f"  Writing {TOTAL_MB} MB ({'os.urandom' if use_urandom else 'fast PRNG'})...", flush=True)

    start = time.perf_counter()
    try:
        with open(path, "wb") as f:
            written = 0
            while written < total_bytes:
                size = min(chunk_bytes, total_bytes - written)
                if use_urandom:
                    data = os.urandom(size)
                else:
                    data = rng.randbytes(size)
                f.write(data)
                written += size
    except OSError as e:
        print(f"  Error: {e}")
        return None
    end = time.perf_counter()

    elapsed = end - start
    mb_per_sec = TOTAL_MB / elapsed

    try:
        path.unlink()
    except OSError:
        pass

    print(f"  Done: {elapsed:.2f} sec -> {mb_per_sec:.1f} MB/s")
    return mb_per_sec


def main():
    print(f"Benchmarking G: drive write speed ({TOTAL_MB} MB, {CHUNK_MB} MB chunks)", flush=True)
    print()

    # Test 1: os.urandom (current Sentinel approach)
    print("1. os.urandom (current):")
    urandom_mbps = benchmark_write(use_urandom=True)
    print()

    # Test 2: Fast PRNG (potential optimization)
    print("2. Fast PRNG:")
    fast_mbps = benchmark_write(use_urandom=False)
    print()

    if urandom_mbps and fast_mbps:
        print(f"Result: Fast PRNG is {fast_mbps / urandom_mbps:.0f}x faster")
        print(f"True disk throughput (estimate): ~{fast_mbps:.1f} MB/s")


if __name__ == "__main__":
    main()

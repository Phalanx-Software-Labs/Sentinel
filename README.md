# Sentinel
Sentinel is an early warning system for MicroSD health. It performs "Quick" and "In-Depth" write-verify scans to detect failing cells before data loss occurs. Warning: This is a hardware stress test. It does not heal cards and may accelerate failure on degraded media. Provided "as is" with liability capped at $1.00. Back up first.
# Sentinel — Standing vigil

**Early warning for your SD card.** Sentinel checks your card before it fails: quick checks and full sweeps, with no permanent footprint. For handhelds, cameras, and anyone who trusts a card with what matters.

---

## Download & install (Windows)

1. Go to [Releases](https://github.com/Phalanx-Software-Labs/Sentinel/releases) and download **Sentinel_Setup.exe** for the latest version.
2. Run the installer and follow the steps.
3. Launch **Sentinel** from the Start Menu or desktop.

No Python or extra runtimes required. You will be asked to accept the End-User License Agreement (EULA) and Terms of Use each time you start Sentinel.

---

## What Sentinel does

- **Quick check** — Writes test data to part of the drive, verifies it by reading and hashing, then deletes it. Fast; leaves no lasting use of space. Good for a regular "is this card still okay?" check.
- **Full sweep** — Verifies every existing file (against a stored manifest) and tests free space. Higher confidence; takes longer. Run when you have time (e.g. card plugged in for an hour).
- **Schedule** — Recommends how often to run a full sweep (e.g. every 7–30 days) based on drive size and type.
- **Honest limits** — Shows approximate confidence (e.g. ~40% for quick check, ~85% for full sweep) and always reminds you: keep backups. Sentinel warns; it does not repair or recover data.

---

## System requirements

- **Windows** (64-bit). Built and tested on Windows 10/11.
- An SD card or other drive you want to test (internal drives work too; use with care).

---

## Run from source (developers)

If you want to hack on Sentinel or run it without the installer:

- **Requirements:** Python 3.x with tkinter (usually included on Windows).
- **Run:** From the project folder:
  python sentinel_ui.py
  

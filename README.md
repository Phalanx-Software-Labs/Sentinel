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

- **Quick check** — Writes test data to part of the drive, verifies it by reading and hashing, then deletes it. Fast; leaves no lasting use of space. Good for a regular “is this card still okay?” check.
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
  ```bash
  python sentinel_ui.py
  ```
- **Install dependencies (if needed):** `pip install -r requirements.txt`

---

## Building the installer

To produce **Sentinel_Setup.exe** for distribution:

1. Install [Inno Setup](https://jrsoftware.org/isdl.php) (default options).
2. From the project folder, in PowerShell:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".\build_installer.ps1"
   ```
3. If `iscc` is not on your PATH, build the installer manually: open **installer.iss** in Inno Setup Compiler and use **Build → Compile**.

The script creates `dist\Sentinel.exe`; Inno Setup creates `Output\Sentinel_Setup.exe`. That’s the file to give to users.

See **HOW_TO_MAKE_THE_INSTALLER.md** for a step-by-step guide.

---

## License & terms

Sentinel is offered under the terms in the in-app EULA and Terms of Use. By using the software you agree to those terms (including hardware stress-test risks, limitation of liability, and jurisdiction). See the EULA text in the application or in **sentinel/eula.py** in the source.

---

## Version

**0.5.0** (beta) — Phase 5 packaging; in-app EULA.

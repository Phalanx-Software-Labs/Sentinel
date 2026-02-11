# Building the installer (Sentinel_Setup.exe)

Internal notes for producing the Windows installer. Output goes to `Output\Sentinel_Setup.exe`; that’s the file to host or attach to a GitHub release.

**Prereqs:** Inno Setup installed ([jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)). Default install is fine. If the build script can’t find it, the Output folder won’t get created—install Inno and rerun.

**Steps:**

1. Open PowerShell, `cd` into the project folder (the one with `build_installer.ps1` and the `sentinel` package).
2. Run:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".\build_installer.ps1"
   ```
   Use the Bypass form; plain `.\build_installer.ps1` often hits execution policy. Build takes a couple minutes. You should see “Build complete” for `dist\Sentinel.exe` and, if Inno is on PATH, “Installer complete” for `Output\Sentinel_Setup.exe`.
3. If there’s no Output folder or it says “Inno Setup not found,” install Inno (or add it to PATH) and run the script again.
4. Upload `Output\Sentinel_Setup.exe` wherever you distribute (e.g. GitHub Releases). Users run it, follow the installer, then launch Sentinel from Start Menu or desktop—no Python or extra setup on their side.

**Troubleshooting:** Path issues usually mean the `cd` in step 1 is wrong (must be the folder containing `build_installer.ps1`). “Scripts disabled” means use the full `powershell -ExecutionPolicy Bypass -File ...` command.

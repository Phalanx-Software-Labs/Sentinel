# How to make the installer people can download and run

You want one file (Sentinel_Setup.exe) that someone can download, double-click, and install Sentinel. Here’s how to create that file **on your computer**. They never see any of this.

---

## Step 1: Install “Inno Setup” (one time)

1. Open your browser and go to: **https://jrsoftware.org/isdl.php**
2. Download **Inno Setup** (the first big download link on that page).
3. Run the downloaded file and click through the installer. Use all the default options (just keep clicking Next, then Finish).
4. You’re done with this step. You only do it once.

---

## Step 2: Open PowerShell in your project folder

1. Press the **Windows key** on your keyboard.
2. Type **powershell**.
3. Click **Windows PowerShell** (the blue icon).
4. A window opens with a line that ends in something like `PS C:\Users\...`
5. Type this **exactly** (or copy and paste it), then press **Enter**:

   ```text
   cd "c:\(PSL) Phalanx Software Labs\sentinel, full project\sentinel-phase2"
   ```

   If your project is in a different folder, change that path to your real folder. The window should now show that path.

---

## Step 3: Run the build script

1. In that same PowerShell window, type this and press **Enter**:

   ```text
   powershell -ExecutionPolicy Bypass -File ".\build_installer.ps1"
   ```

2. Wait. It can take a minute or two. You’ll see a lot of text. When it’s done you should see something like:
   - “Build complete: ...\dist\Sentinel.exe”
   - “Installer complete: ...\Output\Sentinel_Setup.exe”

3. If you see “Inno Setup not found”, go back to Step 1 and make sure Inno Setup is installed, then try Step 3 again.

---

## Step 4: Find the installer file

1. Open **File Explorer** (the folder icon).
2. Go to your project folder:  
   `c:\(PSL) Phalanx Software Labs\sentinel, full project\sentinel-phase2`
3. Open the **Output** folder.
4. Inside it you’ll see **Sentinel_Setup.exe**.

That’s the file. **That’s what you give to people.**

---

## What you do with that file

- Put **Sentinel_Setup.exe** wherever you want people to download it from (your website, a file host, GitHub Releases, etc.).
- Tell them: “Download Sentinel_Setup.exe, double-click it, and follow the installer.”
- They don’t need Python, PowerShell, or anything else. Double-click → install → they can run Sentinel from the Start Menu or desktop.

---

## If something goes wrong

- **“Running scripts is disabled”**  
  You must use the long command in Step 3 (the one that starts with `powershell -ExecutionPolicy Bypass -File`). Don’t just type `.\build_installer.ps1`.

- **“Inno Setup not found” or no Output folder**  
  Install Inno Setup from Step 1 and run Step 3 again.

- **Path or folder errors**  
  Make sure the path in Step 2 is the folder that contains `build_installer.ps1` and the `sentinel` folder. If your project lives somewhere else, change the path in Step 2 to that folder.

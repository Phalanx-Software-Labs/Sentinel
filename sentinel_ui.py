"""Sentinel standalone UI."""

import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading

from sentinel import __version__
from sentinel.eula import EULA_TEXT
from sentinel.drive import get_available_drives
from sentinel.config import load_config, save_config
from sentinel.core import quick_check
from sentinel.sweep import full_sweep, sweep_due
from sentinel.recommendation import (
    recommend_schedule,
    get_quality_warnings,
    recommend_check_size_fraction,
)


class SentinelUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Sentinel {__version__} — Standing vigil")
        self.root.minsize(420, 320)
        self.root.resizable(True, True)

        self.drive_var = tk.StringVar()
        self.result_var = tk.StringVar(value="—")
        self.progress_var = tk.StringVar(value="")
        self.sweep_due_var = tk.StringVar(value="")
        self.operation_running = False
        self.operation_thread = None
        self._verification_details_text = ""
        self._abort_requested = False

        # Show EULA first; main UI is built after user agrees
        self._build_eula_screen()

    def _build_eula_screen(self):
        """Show EULA; user must scroll to bottom and click I Agree to continue."""
        self._eula_frame = ttk.Frame(self.root, padding=15)
        self._eula_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            self._eula_frame,
            text="Please read the following agreement. Scroll to the bottom to enable \"I Agree\".",
            wraplength=500,
        ).pack(anchor=tk.W, pady=(0, 8))

        text_frame = ttk.Frame(self._eula_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._eula_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=self._make_eula_scroll_command(scrollbar),
            state=tk.DISABLED,
            font=("Segoe UI", 9),
            width=72,
            height=24,
        )
        self._eula_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._eula_text.yview)

        self._eula_text.config(state=tk.NORMAL)
        self._eula_text.insert(tk.END, EULA_TEXT)
        self._eula_text.config(state=tk.DISABLED)

        def after_scroll(_event=None):
            self.root.after(50, self._check_eula_scrolled_to_bottom)

        self._eula_text.bind("<MouseWheel>", after_scroll)
        self._eula_text.bind("<Button-4>", after_scroll)
        self._eula_text.bind("<Button-5>", after_scroll)

        btn_frame = ttk.Frame(self._eula_frame)
        btn_frame.pack(fill=tk.X)
        self._eula_agree_btn = ttk.Button(
            btn_frame,
            text="I Agree",
            command=self._on_eula_agree,
            state="disabled",
        )
        self._eula_agree_btn.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="I Do Not Agree", command=self.root.quit).pack(side=tk.LEFT)

        # Check scroll state after layout (in case text fits without scrolling)
        self.root.after(100, self._check_eula_scrolled_to_bottom)

    def _make_eula_scroll_command(self, scrollbar):
        """Wrap scrollbar.set so we also check if user scrolled to bottom."""

        def on_scroll(*args):
            scrollbar.set(*args)
            self._check_eula_scrolled_to_bottom()

        return on_scroll

    def _check_eula_scrolled_to_bottom(self):
        """Enable I Agree only when user has scrolled to the bottom."""
        try:
            if self._eula_text.yview()[1] >= 0.999:
                self._eula_agree_btn.state(["!disabled"])
        except (AttributeError, tk.TclError):
            pass

    def _on_eula_agree(self):
        """User agreed to EULA; show main app."""
        self._eula_frame.destroy()
        del self._eula_frame
        del self._eula_text
        del self._eula_agree_btn
        self._build_ui()
        self._load_drives_and_config()
        self.interval_combo.bind("<<ComboboxSelected>>", self._on_interval_change)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # Drive selector
        ttk.Label(main, text="Drive:").pack(anchor=tk.W)
        self.drive_combo = ttk.Combobox(
            main, textvariable=self.drive_var, state="readonly", width=40
        )
        self.drive_combo.pack(fill=tk.X, pady=(0, 5))
        self.drive_combo.bind("<<ComboboxSelected>>", self._on_drive_change)

        # Sweep due / interval
        interval_frame = ttk.Frame(main)
        interval_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(interval_frame, text="Full sweep interval:").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value="14")
        self.interval_combo = ttk.Combobox(
            interval_frame,
            textvariable=self.interval_var,
            values=["7", "14", "21", "30"],
            state="readonly",
            width=6,
        )
        self.interval_combo.pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(interval_frame, text="days").pack(side=tk.LEFT)
        self.sweep_due_label = ttk.Label(main, textvariable=self.sweep_due_var)
        self.sweep_due_label.pack(anchor=tk.W, pady=(0, 5))
        self.recommendation_var = tk.StringVar(value="")
        self.recommendation_label = ttk.Label(
            main, textvariable=self.recommendation_var, wraplength=400
        )
        self.recommendation_label.pack(anchor=tk.W, pady=(0, 5))
        self.warnings_var = tk.StringVar(value="")
        self.warnings_label = ttk.Label(
            main, textvariable=self.warnings_var, wraplength=400, foreground="orange"
        )
        self.warnings_label.pack(anchor=tk.W, pady=(0, 5))
        self.last_check_var = tk.StringVar(value="")
        self.last_check_label = ttk.Label(
            main, textvariable=self.last_check_var, wraplength=400, font=("", 8)
        )
        self.last_check_label.pack(anchor=tk.W, pady=(0, 10))

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        self.run_btn = ttk.Button(
            btn_frame, text="Run quick check", command=self._on_quick_check_click
        )
        self.run_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.sweep_btn = ttk.Button(
            btn_frame, text="Run full sweep now", command=self._on_full_sweep_click
        )
        self.sweep_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.abort_btn = ttk.Button(
            btn_frame, text="Abort", command=self._on_abort_click, state="disabled"
        )
        self.abort_btn.pack(side=tk.LEFT)

        # Progress
        self.progress_label = ttk.Label(main, textvariable=self.progress_var)
        self.progress_label.pack(pady=(0, 5))

        self.progress_bar = ttk.Progressbar(main, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(0, 15))

        # Result
        ttk.Label(main, text="Result:", font=("", 10, "bold")).pack(anchor=tk.W)
        self.result_label = ttk.Label(
            main, textvariable=self.result_var, wraplength=400
        )
        self.result_label.pack(anchor=tk.W, pady=(0, 5))

        # Verification details — Copy button only
        ttk.Button(main, text="Copy verification details", command=self._copy_verification).pack(anchor=tk.W, pady=(10, 0))

        # Confidence disclaimer
        ttk.Label(
            main,
            text="Quick check: ~40%. Full sweep: ~85%. Always keep backups.",
            font=("", 8),
            foreground="gray",
            wraplength=400,
        ).pack(anchor=tk.W, pady=(10, 0))

    def _load_drives_and_config(self):
        drives = get_available_drives()
        self.drive_combo["values"] = drives
        if not drives:
            self.result_var.set("No drives found.")
            self.run_btn.state(["disabled"])
            self.sweep_btn.state(["disabled"])
            return
        config = load_config()
        last = config.get("last_drive")
        if last and last in drives:
            self.drive_var.set(last)
        else:
            self.drive_var.set(drives[0])
        interval = config.get("sweep_interval_days", 14)
        self.interval_var.set(str(interval))
        self._update_sweep_due()

    def _update_sweep_due(self):
        drive = self._get_drive()
        if not drive:
            self.sweep_due_var.set("")
            self.recommendation_var.set("")
            self.warnings_var.set("")
            self.last_check_var.set("")
            return
        try:
            interval = int(self.interval_var.get())
        except ValueError:
            interval = 14
        due = sweep_due(drive, interval)
        if due:
            self.sweep_due_var.set("Full sweep due.")
        else:
            self.sweep_due_var.set("Full sweep not yet due.")
        # Schedule recommendation
        rec_interval, rec_hint = recommend_schedule(drive)
        self.recommendation_var.set(rec_hint)
        # Quality warnings
        warnings = get_quality_warnings(drive)
        self.warnings_var.set("; ".join(warnings) if warnings else "")
        # Last check / sweep
        config = load_config()
        lines = []
        lct = config.get("last_check_time")
        if lct:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(lct)
                lines.append(f"Last quick check: {dt.strftime('%Y-%m-%d %H:%M')}")
            except (ValueError, TypeError):
                pass
        from sentinel.sweep import read_last_sweep_timestamp

        ts = read_last_sweep_timestamp(drive) if drive else None
        if ts:
            lines.append(f"Last full sweep: {ts.strftime('%Y-%m-%d %H:%M')}")
        elif config.get("last_sweep_time"):
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(config["last_sweep_time"])
                lines.append(f"Last full sweep: {dt.strftime('%Y-%m-%d %H:%M')}")
            except (ValueError, TypeError, KeyError):
                pass
        self.last_check_var.set(" | ".join(lines) if lines else "")

    def _format_verification_details(self, result: dict, check_type: str) -> str:
        """Format verification_details for display/copy."""
        if check_type == "quick_check":
            vd = result.get("verification_details", [])
            if not vd:
                return "(no verification data)"
            lines = ["=== Quick Check Verification ==="]
            for d in vd:
                exp = d.get("expected_hash", "?")
                r1 = d.get("read1_hash", "?")
                r2 = d.get("read2_hash", "?")
                match = "yes" if d.get("match") else "NO"
                lines.append(f"Batch {d.get('batch', '?')}: expected {exp} | read1 {r1} | read2 {r2} | Match: {match}")
            return "\n".join(lines)
        elif check_type == "full_sweep":
            vd = result.get("verification_details", {})
            manifest_vd = vd.get("manifest", [])
            free_vd = vd.get("free_space", [])
            lines = ["=== Full Sweep Verification ==="]
            if manifest_vd:
                lines.append("--- Manifest (file verification) ---")
                for d in manifest_vd:
                    path = d.get("path", "?")
                    exp = d.get("expected_hash", "?")
                    read_h = d.get("read_hash", "?")
                    match = "yes" if d.get("match") else "NO"
                    note = f" [{d.get('note', '')}]" if d.get("note") else ""
                    lines.append(f"{path}: expected {exp} | read {read_h} | Match: {match}{note}")
            if free_vd:
                lines.append("--- Free Space ---")
                for d in free_vd:
                    exp = d.get("expected_hash", "?")
                    r1 = d.get("read1_hash", "?")
                    r2 = d.get("read2_hash", "?")
                    match = "yes" if d.get("match") else "NO"
                    lines.append(f"Batch {d.get('batch', '?')}: expected {exp} | read1 {r1} | read2 {r2} | Match: {match}")
            if not manifest_vd and not free_vd:
                return "(no verification data)"
            return "\n".join(lines)
        return "(unknown)"

    def _copy_verification(self):
        if self._verification_details_text.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(self._verification_details_text)

    def _get_drive(self) -> str | None:
        drive = self.drive_var.get().strip()
        if not drive:
            return None
        return drive + "\\" if not drive.endswith("\\") else drive

    def _on_drive_change(self, event=None):
        save_config(last_drive=self.drive_var.get())
        self._update_sweep_due()

    def _on_interval_change(self, event=None):
        try:
            interval = int(self.interval_var.get())
            save_config(sweep_interval_days=interval)
            self._update_sweep_due()
        except ValueError:
            pass

    def _on_quick_check_click(self):
        if self.operation_running:
            return
        drive = self._get_drive()
        if not drive:
            messagebox.showwarning("Sentinel", "Please select a drive.")
            return
        size_frac = recommend_check_size_fraction(drive)
        self._start_quick_check(drive, size_frac)

    def _on_abort_click(self):
        self._abort_requested = True

    def _on_full_sweep_click(self):
        if self.operation_running:
            return
        drive = self._get_drive()
        if not drive:
            messagebox.showwarning("Sentinel", "Please select a drive.")
            return
        if not messagebox.askyesno(
            "Sentinel",
            "Full sweep can take 1+ hours. It will run in the background. Continue?",
        ):
            return
        self._start_full_sweep(drive)

    def _set_buttons_enabled(self, enabled: bool):
        state = [] if enabled else ["disabled"]
        self.run_btn.state(state)
        self.sweep_btn.state(state)
        self.abort_btn.state(["disabled"] if enabled else ["!disabled"])

    def _start_quick_check(self, drive: str, size_frac: float):
        self.operation_running = True
        self._abort_requested = False
        self._set_buttons_enabled(False)
        self.result_var.set("Running…")
        self.progress_var.set("")
        self._verification_details_text = ""
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 100
        start_time = time.time()

        def _format_remaining(sec: float) -> str:
            if sec < 60:
                return f"~{int(sec)} sec"
            m, s = divmod(int(sec), 60)
            if s == 0:
                return f"~{m} min"
            return f"~{m} min {s} sec"

        def progress_cb(current, total, message):
            def update():
                if total > 0:
                    pct = 100 * current / total
                    self.progress_bar["value"] = pct
                    elapsed = time.time() - start_time
                    if current > 0 and current < total:
                        rate = elapsed / current
                        remaining_sec = rate * (total - current)
                        self.progress_var.set(
                            f"{message} — {_format_remaining(remaining_sec)} remaining"
                        )
                    else:
                        self.progress_var.set(message)
                else:
                    self.progress_var.set(message)
                self.root.after(0, update)

        def run():
            result = quick_check(
                drive,
                size_frac,
                progress_callback=progress_cb,
                abort_check=lambda: self._abort_requested,
            )
            self.root.after(0, lambda: self._on_quick_check_done(result))

        self.operation_thread = threading.Thread(target=run, daemon=True)
        self.operation_thread.start()

    def _on_quick_check_done(self, result: dict):
        self.operation_running = False
        self._abort_requested = False
        self._set_buttons_enabled(True)
        self.progress_bar["value"] = 100
        self.progress_var.set("Done.")

        passed = result.get("passed", False)
        msg = result.get("message", "Unknown")
        details = result.get("details", "")
        aborted = result.get("aborted", False)

        if aborted:
            confidence = result.get("extrapolated_confidence_pct")
            self.result_var.set(
                f"Aborted — {msg}\n{details}"
                + (f" (extrapolated confidence: ~{confidence}%)" if confidence is not None else "")
            )
            self.result_label.configure(foreground="red")
        elif passed:
            self.result_var.set(f"Pass — {msg}")
            self.result_label.configure(foreground="")
        else:
            self.result_var.set(f"Fail — {msg}")
            if details:
                self.result_var.set(f"Fail — {msg}\n{details}")
            self.result_label.configure(foreground="red")

        self._verification_details_text = self._format_verification_details(result, "quick_check")

        from datetime import datetime

        save_config(
            last_drive=self.drive_var.get(),
            last_check_time=datetime.now().isoformat(),
        )
        self._update_sweep_due()

    def _start_full_sweep(self, drive: str):
        self.operation_running = True
        self._abort_requested = False
        self._set_buttons_enabled(False)
        self.result_var.set("Full sweep running (can take 1+ hours)…")
        self.progress_var.set("")
        self._verification_details_text = ""
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 100
        start_time = time.time()

        def _format_remaining(sec: float) -> str:
            if sec < 60:
                return f"~{int(sec)} sec"
            m, s = divmod(int(sec), 60)
            if s == 0:
                return f"~{m} min"
            return f"~{m} min {s} sec"

        def progress_cb(current, total, message):
            def update():
                if total > 0:
                    pct = 100 * current / total
                    self.progress_bar["value"] = pct
                elapsed = time.time() - start_time
                if total > 0 and current > 0 and current < total:
                    rate = elapsed / current
                    remaining_sec = rate * (total - current)
                    self.progress_var.set(
                        f"{message} — {_format_remaining(remaining_sec)} remaining"
                    )
                else:
                    self.progress_var.set(message)
            self.root.after(0, update)

        def run():
            result = full_sweep(
                drive,
                progress_callback=progress_cb,
                manifest_callback=lambda p: self.root.after(
                    0, lambda phase=p: self.progress_var.set(f"Phase: {phase}…")
                ),
                abort_check=lambda: self._abort_requested,
            )
            self.root.after(0, lambda: self._on_full_sweep_done(result))

        self.operation_thread = threading.Thread(target=run, daemon=True)
        self.operation_thread.start()

    def _on_full_sweep_done(self, result: dict):
        self.operation_running = False
        self._abort_requested = False
        self._set_buttons_enabled(True)
        self.progress_bar["value"] = 100
        self.progress_var.set("Done.")

        passed = result.get("passed", False)
        msg = result.get("message", "Unknown")
        details = result.get("details", "")
        m_ok = result.get("manifest_passed", True)
        fs_ok = result.get("free_space_passed", True)
        aborted = result.get("aborted", False)

        if aborted:
            self.result_var.set(f"Aborted — {msg}\n{details}")
            self.result_label.configure(foreground="red")
        elif passed:
            self.result_var.set(f"Pass — {msg}\n{details}")
            self.result_label.configure(foreground="")
        else:
            parts = [f"Fail — {msg}"]
            if not m_ok:
                parts.append("File verification failed.")
            if not fs_ok:
                parts.append("Free-space sweep failed.")
            if details:
                parts.append(details)
            self.result_var.set("\n".join(parts))
            self.result_label.configure(foreground="red")

        self._verification_details_text = self._format_verification_details(result, "full_sweep")

        from datetime import datetime

        save_config(
            last_drive=self.drive_var.get(),
            last_sweep_time=datetime.now().isoformat(),
        )
        self._update_sweep_due()

    def run(self):
        self.root.mainloop()


def main():
    app = SentinelUI()
    app.run()


if __name__ == "__main__":
    main()

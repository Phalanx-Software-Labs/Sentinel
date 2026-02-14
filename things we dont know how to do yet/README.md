# Things We Don't Know How To Do Yet

---

## 1. Be taller

The rest are real. We hope. We promise.

---

## 2. Make the scan of existing files optional

- **What:** Allow users to turn off the "verify existing files" (manifest build/verify) part of a full sweep.
- **Why:** Some users may want to test only free space (write/verify) without Sentinel reading every file on the card. Makes the "invasive" file read an opt-in choice.
- **Rough approach:** Add a UI option (e.g. checkbox or scan mode) like "Include file verification" / "Verify existing files." When unchecked, full sweep would skip manifest build/load and verify, and only run the free-space sweep.

---

## 3. Optional "self-sandboxing" mode (firewall)

- **What:** An optional mode where Sentinel checks whether a firewall is blocking it from contacting the web, and can offer to create a firewall rule that **only** affects Sentinel (blocks Sentinel from the internet).
- **Why:** Extra assurance for privacy-minded users: even if the app were ever changed to try to phone home, a Sentinel-only block would prevent it. Optional and user-initiated.
- **Rough approach:**
  - Detect if a firewall exists (e.g. Windows Firewall).
  - Optionally test outbound connectivity (or just offer the rule).
  - Offer to create an outbound block rule for Sentinel's executable(s) only.
  - Document that this only affects Sentinel, not other apps.

---

## 4. Make full scan faster without sacrificing too much accuracy

- **What:** Speed up the full sweep (file verification + free-space sweep) while keeping results trustworthy.
- **Ideas to explore:**
  - **Parallel reads:** Hash multiple files in parallel (e.g. thread pool or async I/O) where the drive/OS can handle it.
  - **Larger read chunks** for hashing if it doesn't hurt accuracy.
  - **Optional same-run double read:** Add an option to do two reads of each file in one run and compare (read consistency); consider making it optional so users can trade time for that extra check.
  - **Smarter ordering:** e.g. read large files in bigger chunks, or batch small files, to reduce overhead.
  - **Progress/cancellation:** Ensure abort and progress still work so long runs feel responsive.
- **Constraint:** Don't sacrifice accuracy meaningfully; document any trade-offs (e.g. "faster mode skips second read").

---

*Last updated: February 2026*

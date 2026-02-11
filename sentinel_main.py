"""Sentinel — Entry point. Load config, show window, run."""

import sys
import os

# Ensure project root is on path for 'sentinel' package
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sentinel_ui import main

if __name__ == "__main__":
    main()

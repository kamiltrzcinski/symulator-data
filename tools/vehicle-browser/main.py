#!/usr/bin/env python3
"""vehicle-browser — GUI browser for symulator-data vehicle types and vehicles."""

import sys
from pathlib import Path

# Allow running from the tools/vehicle-browser/ directory or as PyInstaller bundle
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow


def find_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in [here, here.parent, here.parent.parent]:
        if (candidate / "data").exists():
            return candidate
    return here.parent.parent


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else find_repo_root()
    MainWindow(root).run()

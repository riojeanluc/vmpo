"""Small helpers shared by scanners; keeps Windows-only API calls isolated
so the rest of the codebase stays testable on any OS."""
from __future__ import annotations

import subprocess
import sys


def is_windows() -> bool:
    return sys.platform == "win32"


def is_process_running(process_name: str) -> bool:
    """Best-effort check via `tasklist`. Returns False (not blocking) if the
    check itself fails, since scanning must never crash on a locked file."""
    if not is_windows():
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        return process_name.lower() in result.stdout.lower()
    except OSError:
        return False

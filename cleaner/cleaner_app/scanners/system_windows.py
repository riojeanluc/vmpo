"""Scanners for Windows system-level cleanup targets: user/system temp
directories and the Recycle Bin."""
from __future__ import annotations

import ctypes
import os
import time
from pathlib import Path
from typing import Iterable, List, Optional

from ..models import Action, Target
from ..platform_utils import is_windows


def _iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            yield Path(dirpath) / name


def scan_temp_dirs(min_age_days: int = 3) -> List[Target]:
    """Scan %TEMP%/%TMP% and C:\\Windows\\Temp for files older than
    min_age_days. Age filtering avoids deleting files a running app is
    still writing to."""
    targets: List[Target] = []
    cutoff = time.time() - min_age_days * 86400

    candidates = {
        os.environ.get("TEMP"),
        os.environ.get("TMP"),
        r"C:\Windows\Temp" if is_windows() else None,
    }

    for raw_path in filter(None, candidates):
        root = Path(raw_path)
        for file_path in _iter_files(root):
            try:
                stat = file_path.stat()
            except OSError:
                continue
            if stat.st_mtime > cutoff:
                continue
            targets.append(Target(
                category="system",
                subcategory="temp",
                path=str(file_path),
                description=f"Fichier temporaire ({root.name})",
                size_bytes=stat.st_size,
                action=Action.DELETE_FILE,
            ))
    return targets


def scan_recycle_bin() -> List[Target]:
    """Query the Recycle Bin's total size via SHQueryRecycleBinW."""
    if not is_windows():
        return []

    class SHQUERYRBINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_uint32),
            ("i64Size", ctypes.c_int64),
            ("i64NumItems", ctypes.c_int64),
        ]

    info = SHQUERYRBINFO()
    info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
    if result != 0 or info.i64NumItems == 0:
        return []

    return [Target(
        category="system",
        subcategory="recycle_bin",
        path="Recycle Bin",
        description=f"{info.i64NumItems} élément(s) dans la Corbeille",
        size_bytes=info.i64Size,
        action=Action.EMPTY_RECYCLE_BIN,
    )]

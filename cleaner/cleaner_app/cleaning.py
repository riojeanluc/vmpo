"""Executes cleanup actions for a list of selected Targets. Every action is
dry-run by default: nothing is deleted unless dry_run=False is passed
explicitly (the CLI only does so behind --yes)."""
from __future__ import annotations

import ctypes
import logging
import os
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .models import Action, Target
from .platform_utils import is_windows

logger = logging.getLogger("cleaner_app")

_CHROMIUM_CLEAR_SQL = ("DELETE FROM visits;", "DELETE FROM urls;")
_FIREFOX_CLEAR_SQL = (
    "DELETE FROM moz_historyvisits;",
    "DELETE FROM moz_places WHERE id NOT IN "
    "(SELECT DISTINCT fk FROM moz_bookmarks WHERE fk IS NOT NULL);",
)


@dataclass
class CleanResult:
    target: Target
    ok: bool
    skipped_reason: Optional[str] = None


def _clear_sqlite_history(target: Target) -> None:
    statements = _CHROMIUM_CLEAR_SQL if target.meta.get("engine") == "chromium" else _FIREFOX_CLEAR_SQL
    with sqlite3.connect(target.path, timeout=1) as conn:
        for statement in statements:
            conn.execute(statement)
        conn.commit()
        conn.execute("VACUUM;")


def _delete_dir_contents(path: Path) -> None:
    for entry in path.iterdir():
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
        else:
            entry.unlink(missing_ok=True)


def _empty_recycle_bin() -> None:
    sherb_no_confirmation, sherb_no_progress_ui, sherb_no_sound = 0x1, 0x2, 0x4
    ctypes.windll.shell32.SHEmptyRecycleBinW(
        None, None, sherb_no_confirmation | sherb_no_progress_ui | sherb_no_sound
    )


def clean(targets: List[Target], dry_run: bool = True) -> List[CleanResult]:
    results: List[CleanResult] = []
    for target in targets:
        if dry_run:
            logger.info("[DRY RUN] would clean: %s (%s Mo)", target.path, target.size_mb())
            results.append(CleanResult(target, ok=True, skipped_reason="dry-run"))
            continue

        try:
            if target.action == Action.DELETE_FILE:
                os.remove(target.path)
            elif target.action == Action.DELETE_DIR_CONTENTS:
                _delete_dir_contents(Path(target.path))
            elif target.action == Action.EMPTY_RECYCLE_BIN:
                if not is_windows():
                    raise OSError("Recycle Bin cleanup is Windows-only")
                _empty_recycle_bin()
            elif target.action == Action.CLEAR_SQLITE_HISTORY:
                _clear_sqlite_history(target)
            else:
                raise ValueError(f"Unknown action: {target.action}")

            logger.info("cleaned: %s (%s Mo)", target.path, target.size_mb())
            results.append(CleanResult(target, ok=True))
        except (OSError, sqlite3.Error) as exc:
            logger.warning("skipped %s: %s", target.path, exc)
            results.append(CleanResult(target, ok=False, skipped_reason=str(exc)))
    return results

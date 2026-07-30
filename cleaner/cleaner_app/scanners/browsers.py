"""Scanners for browser history/cache cleanup targets (Chromium-based
browsers and Firefox)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import List, Optional

from ..models import Action, Target

# Path parts relative to %LOCALAPPDATA%, kept as tuples (not raw Windows
# strings) so path joining stays correct on every OS during tests.
_CHROMIUM_BROWSERS = {
    "chrome": ("Google", "Chrome", "User Data"),
    "edge": ("Microsoft", "Edge", "User Data"),
    "brave": ("BraveSoftware", "Brave-Browser", "User Data"),
}


def _dir_size(path: Path) -> int:
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for name in filenames:
            try:
                total += (Path(dirpath) / name).stat().st_size
            except OSError:
                pass
    return total


def _count_rows(db_path: Path, query: str) -> Optional[int]:
    """Best-effort row count. Returns None if the DB is locked (browser
    open) or otherwise unreadable — that's not an error, it just means the
    count can't be shown yet."""
    try:
        uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=1) as conn:
            return conn.execute(query).fetchone()[0]
    except sqlite3.Error:
        return None


def scan_chromium_profiles(local_app_data: Optional[str] = None) -> List[Target]:
    base = Path(local_app_data or os.environ.get("LOCALAPPDATA", ""))
    targets: List[Target] = []

    for browser_name, relative_parts in _CHROMIUM_BROWSERS.items():
        user_data = base.joinpath(*relative_parts)
        if not user_data.exists():
            continue
        for profile_dir in user_data.glob("*"):
            is_profile = profile_dir.name == "Default" or profile_dir.name.startswith("Profile ")
            if not profile_dir.is_dir() or not is_profile:
                continue

            history_db = profile_dir / "History"
            if history_db.exists():
                url_count = _count_rows(history_db, "SELECT COUNT(*) FROM urls")
                description = f"{browser_name} / {profile_dir.name} — historique"
                if url_count is not None:
                    description += f" ({url_count} entrées)"
                targets.append(Target(
                    category="browser", subcategory=f"{browser_name}_history",
                    path=str(history_db), description=description,
                    size_bytes=history_db.stat().st_size,
                    action=Action.CLEAR_SQLITE_HISTORY,
                    meta={"engine": "chromium"},
                ))

            cache_dir = profile_dir / "Cache"
            if cache_dir.exists():
                targets.append(Target(
                    category="browser", subcategory=f"{browser_name}_cache",
                    path=str(cache_dir),
                    description=f"{browser_name} / {profile_dir.name} — cache",
                    size_bytes=_dir_size(cache_dir),
                    action=Action.DELETE_DIR_CONTENTS,
                ))
    return targets


def scan_firefox_profiles(app_data: Optional[str] = None) -> List[Target]:
    base = Path(app_data or os.environ.get("APPDATA", ""))
    profiles_root = base / "Mozilla" / "Firefox" / "Profiles"
    targets: List[Target] = []
    if not profiles_root.exists():
        return targets

    for profile_dir in profiles_root.glob("*"):
        if not profile_dir.is_dir():
            continue

        places_db = profile_dir / "places.sqlite"
        if places_db.exists():
            url_count = _count_rows(places_db, "SELECT COUNT(*) FROM moz_places")
            description = f"firefox / {profile_dir.name} — historique"
            if url_count is not None:
                description += f" ({url_count} entrées)"
            targets.append(Target(
                category="browser", subcategory="firefox_history",
                path=str(places_db), description=description,
                size_bytes=places_db.stat().st_size,
                action=Action.CLEAR_SQLITE_HISTORY,
                meta={"engine": "firefox"},
            ))

        cache_dir = profile_dir / "cache2"
        if cache_dir.exists():
            targets.append(Target(
                category="browser", subcategory="firefox_cache",
                path=str(cache_dir),
                description=f"firefox / {profile_dir.name} — cache",
                size_bytes=_dir_size(cache_dir),
                action=Action.DELETE_DIR_CONTENTS,
            ))
    return targets


def scan_all_browsers() -> List[Target]:
    return scan_chromium_profiles() + scan_firefox_profiles()

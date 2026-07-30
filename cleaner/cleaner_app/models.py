"""Data model for a cleanable item discovered during a scan."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Action(str, Enum):
    DELETE_FILE = "delete_file"
    DELETE_DIR_CONTENTS = "delete_dir_contents"
    EMPTY_RECYCLE_BIN = "empty_recycle_bin"
    CLEAR_SQLITE_HISTORY = "clear_sqlite_history"
    SSH_DELETE_DIR = "ssh_delete_dir"
    SSH_EMPTY_DIR = "ssh_empty_dir"


@dataclass
class Target:
    category: str          # "system" or "browser"
    subcategory: str       # e.g. "temp", "recycle_bin", "chrome_history", "firefox_cache"
    path: str
    description: str
    size_bytes: int = 0
    action: Action = Action.DELETE_FILE
    meta: dict = field(default_factory=dict)

    def size_mb(self) -> float:
        return round(self.size_bytes / (1024 * 1024), 2)

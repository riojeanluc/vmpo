import os
import time
from pathlib import Path

from cleaner_app.scanners.system_windows import scan_temp_dirs


def test_scan_temp_dirs_only_returns_old_files(tmp_path, monkeypatch):
    monkeypatch.setenv("TEMP", str(tmp_path))
    monkeypatch.delenv("TMP", raising=False)

    old_file = tmp_path / "old.tmp"
    old_file.write_text("old")
    old_time = time.time() - 10 * 86400
    os.utime(old_file, (old_time, old_time))

    new_file = tmp_path / "new.tmp"
    new_file.write_text("new")

    targets = scan_temp_dirs(min_age_days=3)

    paths = {Path(t.path) for t in targets}
    assert old_file in paths
    assert new_file not in paths


def test_scan_temp_dirs_empty_when_no_env_set(monkeypatch):
    monkeypatch.delenv("TEMP", raising=False)
    monkeypatch.delenv("TMP", raising=False)

    assert scan_temp_dirs() == []

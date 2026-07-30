import sqlite3
from pathlib import Path

from cleaner_app.cleaning import clean
from cleaner_app.models import Action, Target


def _make_chromium_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT)")
    conn.execute("CREATE TABLE visits (id INTEGER PRIMARY KEY, url INTEGER)")
    conn.execute("INSERT INTO urls (url) VALUES ('https://example.com')")
    conn.execute("INSERT INTO visits (url) VALUES (1)")
    conn.commit()
    conn.close()


def test_clear_chromium_history_removes_rows(tmp_path):
    db_path = tmp_path / "History"
    _make_chromium_db(db_path)

    target = Target(category="browser", subcategory="chrome_history", path=str(db_path),
                     description="test", size_bytes=db_path.stat().st_size,
                     action=Action.CLEAR_SQLITE_HISTORY, meta={"engine": "chromium"})

    results = clean([target], dry_run=False)

    assert results[0].ok
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM urls").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0] == 0


def _make_firefox_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT)")
    conn.execute("CREATE TABLE moz_historyvisits (id INTEGER PRIMARY KEY, place_id INTEGER)")
    conn.execute("CREATE TABLE moz_bookmarks (id INTEGER PRIMARY KEY, fk INTEGER)")
    conn.execute("INSERT INTO moz_places (url) VALUES ('https://bookmarked.example')")  # id 1
    conn.execute("INSERT INTO moz_places (url) VALUES ('https://visited-only.example')")  # id 2
    conn.execute("INSERT INTO moz_historyvisits (place_id) VALUES (1)")
    conn.execute("INSERT INTO moz_historyvisits (place_id) VALUES (2)")
    conn.execute("INSERT INTO moz_bookmarks (fk) VALUES (1)")
    conn.commit()
    conn.close()


def test_clear_firefox_history_preserves_bookmarked_places(tmp_path):
    db_path = tmp_path / "places.sqlite"
    _make_firefox_db(db_path)

    target = Target(category="browser", subcategory="firefox_history", path=str(db_path),
                     description="test", size_bytes=db_path.stat().st_size,
                     action=Action.CLEAR_SQLITE_HISTORY, meta={"engine": "firefox"})

    results = clean([target], dry_run=False)

    assert results[0].ok
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM moz_historyvisits").fetchone()[0] == 0
    remaining_urls = [row[0] for row in conn.execute("SELECT url FROM moz_places").fetchall()]
    assert remaining_urls == ["https://bookmarked.example"]


def test_dry_run_does_not_delete(tmp_path):
    db_path = tmp_path / "History"
    _make_chromium_db(db_path)
    target = Target(category="browser", subcategory="chrome_history", path=str(db_path),
                     description="test", size_bytes=db_path.stat().st_size,
                     action=Action.CLEAR_SQLITE_HISTORY, meta={"engine": "chromium"})

    results = clean([target], dry_run=True)

    assert results[0].skipped_reason == "dry-run"
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM urls").fetchone()[0] == 1


def test_delete_file_action(tmp_path):
    file_path = tmp_path / "temp.log"
    file_path.write_text("data")
    target = Target(category="system", subcategory="temp", path=str(file_path),
                     description="test", size_bytes=4, action=Action.DELETE_FILE)

    results = clean([target], dry_run=False)

    assert results[0].ok
    assert not file_path.exists()


def test_delete_missing_file_is_skipped_not_raised(tmp_path):
    missing = tmp_path / "nope.log"
    target = Target(category="system", subcategory="temp", path=str(missing),
                     description="test", size_bytes=0, action=Action.DELETE_FILE)

    results = clean([target], dry_run=False)

    assert not results[0].ok
    assert results[0].skipped_reason is not None


def test_delete_dir_contents(tmp_path):
    cache_dir = tmp_path / "Cache"
    cache_dir.mkdir()
    (cache_dir / "a.bin").write_bytes(b"x")
    (cache_dir / "sub").mkdir()
    (cache_dir / "sub" / "b.bin").write_bytes(b"y")

    target = Target(category="browser", subcategory="chrome_cache", path=str(cache_dir),
                     description="test", size_bytes=2, action=Action.DELETE_DIR_CONTENTS)

    results = clean([target], dry_run=False)

    assert results[0].ok
    assert list(cache_dir.iterdir()) == []

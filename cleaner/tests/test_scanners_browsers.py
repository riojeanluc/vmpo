import sqlite3

from cleaner_app.scanners.browsers import scan_chromium_profiles, scan_firefox_profiles


def test_scan_chromium_profiles_finds_history_and_cache(tmp_path):
    profile = tmp_path / "Google" / "Chrome" / "User Data" / "Default"
    profile.mkdir(parents=True)

    history_db = profile / "History"
    conn = sqlite3.connect(history_db)
    conn.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT)")
    conn.execute("INSERT INTO urls (url) VALUES ('https://example.com')")
    conn.commit()
    conn.close()

    cache_dir = profile / "Cache"
    cache_dir.mkdir()
    (cache_dir / "entry1").write_bytes(b"x" * 100)

    targets = scan_chromium_profiles(local_app_data=str(tmp_path))

    subcategories = {t.subcategory for t in targets}
    assert "chrome_history" in subcategories
    assert "chrome_cache" in subcategories

    history_target = next(t for t in targets if t.subcategory == "chrome_history")
    assert "1 entrées" in history_target.description

    cache_target = next(t for t in targets if t.subcategory == "chrome_cache")
    assert cache_target.size_bytes == 100


def test_scan_firefox_profiles_finds_history(tmp_path):
    profile = tmp_path / "Mozilla" / "Firefox" / "Profiles" / "abc123.default"
    profile.mkdir(parents=True)

    places_db = profile / "places.sqlite"
    conn = sqlite3.connect(places_db)
    conn.execute("CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT)")
    conn.commit()
    conn.close()

    targets = scan_firefox_profiles(app_data=str(tmp_path))

    assert len(targets) == 1
    assert targets[0].subcategory == "firefox_history"


def test_scan_returns_empty_when_no_profiles(tmp_path):
    assert scan_chromium_profiles(local_app_data=str(tmp_path)) == []
    assert scan_firefox_profiles(app_data=str(tmp_path)) == []

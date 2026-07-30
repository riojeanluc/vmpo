import json

from cleaner_app.cleaning import CleanResult
from cleaner_app.models import Action, Target
from cleaner_app.report import format_clean_report, format_scan_report, targets_to_json


def _target(size_bytes=1024 * 1024):
    return Target(category="system", subcategory="temp", path="/tmp/x",
                   description="fichier test", size_bytes=size_bytes)


def test_format_scan_report_empty():
    assert format_scan_report([]) == "Rien à nettoyer."


def test_format_scan_report_includes_total():
    report = format_scan_report([_target(), _target(size_bytes=2 * 1024 * 1024)])
    assert "3.0 Mo" in report
    assert "2 éléments" in report


def test_format_clean_report_dry_run():
    report = format_clean_report([CleanResult(_target(), ok=True, skipped_reason="dry-run")])
    assert "simulation" in report


def test_format_clean_report_success_and_failure():
    results = [
        CleanResult(_target(), ok=True),
        CleanResult(_target(), ok=False, skipped_reason="Permission denied"),
    ]
    report = format_clean_report(results)
    assert "1 élément(s) nettoyés" in report
    assert "Permission denied" in report


def test_targets_to_json_roundtrip():
    data = json.loads(targets_to_json([_target()]))
    assert data[0]["subcategory"] == "temp"
    assert data[0]["action"] == Action.DELETE_FILE.value

"""Human-readable / JSON summaries of scan and clean results."""
from __future__ import annotations

import json
from typing import List

from .cleaning import CleanResult
from .models import Target


def format_scan_report(targets: List[Target]) -> str:
    if not targets:
        return "Rien à nettoyer."

    lines = []
    total = 0
    for target in sorted(targets, key=lambda t: t.size_bytes, reverse=True):
        lines.append(f"[{target.category}/{target.subcategory}] {target.description} — {target.size_mb()} Mo")
        total += target.size_bytes
    lines.append(f"\nTotal récupérable : {round(total / (1024 * 1024), 2)} Mo ({len(targets)} éléments)")
    return "\n".join(lines)


def format_clean_report(results: List[CleanResult]) -> str:
    ok = [r for r in results if r.ok and r.skipped_reason != "dry-run"]
    dry_run = [r for r in results if r.skipped_reason == "dry-run"]
    failed = [r for r in results if not r.ok]

    freed = sum(r.target.size_bytes for r in ok)
    lines = []
    if dry_run:
        lines.append(f"{len(dry_run)} élément(s) auraient été nettoyés (mode simulation, utilisez --yes pour appliquer).")
    if ok:
        lines.append(f"{len(ok)} élément(s) nettoyés, {round(freed / (1024 * 1024), 2)} Mo libérés.")
    if failed:
        lines.append(f"{len(failed)} élément(s) ignorés (verrouillés ou inaccessibles) :")
        for r in failed:
            lines.append(f"  - {r.target.path}: {r.skipped_reason}")
    return "\n".join(lines)


def targets_to_json(targets: List[Target]) -> str:
    return json.dumps([
        {
            "category": t.category, "subcategory": t.subcategory, "path": t.path,
            "description": t.description, "size_bytes": t.size_bytes, "action": t.action.value,
        }
        for t in targets
    ], ensure_ascii=False, indent=2)

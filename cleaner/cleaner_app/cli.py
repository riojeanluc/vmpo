"""Command-line entry point: `python -m cleaner_app scan|scan-json|clean [options]`."""
from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional, Set

from .cleaning import clean
from .models import Target
from .report import format_clean_report, format_scan_report, targets_to_json
from .scanners.browsers import scan_all_browsers
from .scanners.system_windows import scan_recycle_bin, scan_temp_dirs


def _collect_targets(categories: Set[str], min_age_days: int) -> List[Target]:
    targets: List[Target] = []
    if "system" in categories:
        targets += scan_temp_dirs(min_age_days=min_age_days)
        targets += scan_recycle_bin()
    if "browser" in categories:
        targets += scan_all_browsers()
    return targets


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cleaner_app", description="Nettoyage système et navigateurs (Windows).")
    parser.add_argument("--categories", default="system,browser",
                         help="Catégories à traiter : system,browser (défaut : les deux)")
    parser.add_argument("--min-age-days", type=int, default=3,
                         help="Âge minimum en jours des fichiers temporaires à nettoyer (défaut : 3)")
    parser.add_argument("--log-file", default=None, help="Chemin du fichier de log")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("scan", help="Analyse et affiche ce qui peut être nettoyé (aucune suppression)")
    subparsers.add_parser("scan-json", help="Comme scan, sortie JSON")

    clean_parser = subparsers.add_parser("clean", help="Nettoie les éléments détectés")
    clean_parser.add_argument("--yes", action="store_true",
                               help="Confirme la suppression réelle (sinon : simulation)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        filename=args.log_file, filemode="a",
    )
    if not args.log_file:
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    categories = set(args.categories.split(","))
    targets = _collect_targets(categories, args.min_age_days)

    if args.command == "scan":
        print(format_scan_report(targets))
    elif args.command == "scan-json":
        print(targets_to_json(targets))
    elif args.command == "clean":
        results = clean(targets, dry_run=not args.yes)
        print(format_clean_report(results))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

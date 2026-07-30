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
from .scanners.synology import scan_all as scan_synology
from .scanners.system_windows import scan_recycle_bin, scan_temp_dirs
from .ssh_utils import SSHTarget


def _collect_targets(
    categories: Set[str], min_age_days: int,
    ssh_target: Optional[SSHTarget], volume_roots: List[str],
) -> List[Target]:
    targets: List[Target] = []
    if "system" in categories:
        targets += scan_temp_dirs(min_age_days=min_age_days)
        targets += scan_recycle_bin()
    if "browser" in categories:
        targets += scan_all_browsers()
    if "synology" in categories:
        if ssh_target is None:
            raise SystemExit("--categories synology nécessite --ssh-host et --ssh-user")
        targets += scan_synology(ssh_target, volume_roots, min_age_days=min_age_days)
    return targets


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cleaner_app",
        description="Nettoyage système, navigateurs (Windows) et NAS Synology (via SSH).",
    )
    parser.add_argument("--categories", default="system,browser",
                         help="Catégories à traiter : system,browser,synology (défaut : system,browser)")
    parser.add_argument("--min-age-days", type=int, default=3,
                         help="Âge minimum en jours des fichiers temporaires à nettoyer, "
                              "Windows et Synology @tmp inclus (défaut : 3)")
    parser.add_argument("--log-file", default=None, help="Chemin du fichier de log")

    parser.add_argument("--ssh-host", default=None, help="Adresse du NAS Synology (catégorie synology)")
    parser.add_argument("--ssh-user", default=None, help="Utilisateur SSH sur le NAS")
    parser.add_argument("--ssh-port", type=int, default=22, help="Port SSH (défaut : 22)")
    parser.add_argument("--ssh-key", default=None, help="Chemin vers la clé privée SSH (optionnel)")
    parser.add_argument("--synology-volumes", default="/volume1",
                         help="Racines de volumes à scanner sur le NAS, séparées par des virgules "
                              "(défaut : /volume1)")

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

    ssh_target = None
    if args.ssh_host and args.ssh_user:
        ssh_target = SSHTarget(
            host=args.ssh_host, user=args.ssh_user,
            port=args.ssh_port, identity_file=args.ssh_key,
        )
    volume_roots = [v.strip() for v in args.synology_volumes.split(",") if v.strip()]

    categories = set(args.categories.split(","))
    targets = _collect_targets(categories, args.min_age_days, ssh_target, volume_roots)

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

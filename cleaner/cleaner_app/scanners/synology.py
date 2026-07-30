"""Scanners for a Synology DSM NAS, reached over SSH: @eaDir thumbnail
caches and per-share #recycle bins. Both are DSM-managed and safe to clear
— @eaDir is regenerated on demand, #recycle is just DSM's trash."""
from __future__ import annotations

import shlex
from typing import List, Tuple

from ..models import Action, Target
from ..ssh_utils import SSHTarget

# -prune stops find from descending into a matched @eaDir, both because
# nested @eaDir folders aren't real extra targets and because @eaDir trees
# can be huge (one per folder with thumbnails).
_EADIR_FIND_CMD = "find {root} -type d -iname '@eaDir' -prune -exec du -sb {{}} \\;"

# #recycle sits directly under each shared folder (one level below the
# volume root), so maxdepth keeps this from scanning the whole volume.
_RECYCLE_FIND_CMD = "find {root} -mindepth 1 -maxdepth 2 -type d -iname '#recycle' -exec du -sb {{}} \\;"

# @tmp is DSM's own scratch space (File Station uploads, Package Center,
# ...); only files older than min_age_days are matched, same semantics as
# the Windows temp scanner, so nothing mid-write gets caught.
_TEMP_FIND_CMD = "find {root} -mindepth 1 -type f -mtime +{min_age_days} -exec du -sb {{}} \\;"


def _parse_du_output(output: str) -> List[Tuple[int, str]]:
    entries: List[Tuple[int, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        size_str, _, path = line.partition("\t")
        try:
            entries.append((int(size_str), path))
        except ValueError:
            continue
    return entries


def scan_eadir(ssh: SSHTarget, volume_roots: List[str]) -> List[Target]:
    targets: List[Target] = []
    for root in volume_roots:
        result = ssh.run(_EADIR_FIND_CMD.format(root=shlex.quote(root)))
        for size_bytes, path in _parse_du_output(result.stdout):
            targets.append(Target(
                category="synology", subcategory="eadir",
                path=path, description=f"Cache miniatures @eaDir ({path})",
                size_bytes=size_bytes, action=Action.SSH_DELETE_DIR,
                meta={"ssh": ssh},
            ))
    return targets


def scan_recycle_bins(ssh: SSHTarget, volume_roots: List[str]) -> List[Target]:
    targets: List[Target] = []
    for root in volume_roots:
        result = ssh.run(_RECYCLE_FIND_CMD.format(root=shlex.quote(root)))
        for size_bytes, path in _parse_du_output(result.stdout):
            targets.append(Target(
                category="synology", subcategory="recycle_bin",
                path=path, description=f"Corbeille dossier partagé ({path})",
                size_bytes=size_bytes, action=Action.SSH_EMPTY_DIR,
                meta={"ssh": ssh},
            ))
    return targets


def scan_temp(ssh: SSHTarget, volume_roots: List[str], min_age_days: int = 3) -> List[Target]:
    """One aggregate Target per volume's @tmp folder (not one per file):
    cleaning re-runs the same find filter with -delete, so a single SSH
    round trip covers both scan and clean instead of one per file."""
    targets: List[Target] = []
    for root in volume_roots:
        temp_root = f"{root.rstrip('/')}/@tmp"
        result = ssh.run(_TEMP_FIND_CMD.format(root=shlex.quote(temp_root), min_age_days=min_age_days))
        entries = _parse_du_output(result.stdout)
        if not entries:
            continue
        total_size = sum(size for size, _ in entries)
        targets.append(Target(
            category="synology", subcategory="temp",
            path=temp_root,
            description=(
                f"Fichiers temporaires @tmp de plus de {min_age_days} j "
                f"({len(entries)} fichier(s), {temp_root})"
            ),
            size_bytes=total_size, action=Action.SSH_DELETE_OLD_FILES,
            meta={"ssh": ssh, "min_age_days": min_age_days},
        ))
    return targets


def scan_all(ssh: SSHTarget, volume_roots: List[str], min_age_days: int = 3) -> List[Target]:
    return (
        scan_eadir(ssh, volume_roots)
        + scan_recycle_bins(ssh, volume_roots)
        + scan_temp(ssh, volume_roots, min_age_days=min_age_days)
    )

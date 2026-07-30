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


def scan_all(ssh: SSHTarget, volume_roots: List[str]) -> List[Target]:
    return scan_eadir(ssh, volume_roots) + scan_recycle_bins(ssh, volume_roots)

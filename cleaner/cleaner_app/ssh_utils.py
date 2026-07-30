"""Thin wrapper around the system `ssh` client, used to reach a Synology
NAS. Kept dependency-free (no paramiko) so PyInstaller packaging and the
test environment stay simple; requires an `ssh` binary on PATH (bundled
with Windows 10 1809+ and every Linux/macOS)."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class SSHTarget:
    host: str
    user: str
    port: int = 22
    identity_file: Optional[str] = None

    def _base_command(self) -> List[str]:
        cmd = ["ssh", "-p", str(self.port), "-o", "BatchMode=yes"]
        if self.identity_file:
            cmd += ["-i", self.identity_file]
        cmd.append(f"{self.user}@{self.host}")
        return cmd

    def run(self, remote_command: str, timeout: int = 60) -> subprocess.CompletedProcess:
        """Runs remote_command over SSH. BatchMode=yes makes ssh fail fast
        instead of hanging on an interactive password/host-key prompt."""
        return subprocess.run(
            self._base_command() + [remote_command],
            capture_output=True, text=True, timeout=timeout, check=False,
        )

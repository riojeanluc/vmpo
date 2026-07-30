import subprocess

from cleaner_app.models import Action
from cleaner_app.scanners.synology import scan_all, scan_eadir, scan_recycle_bins, scan_temp


class _FakeSSH:
    """Test double: returns canned output instead of actually running ssh."""

    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    def run(self, remote_command, timeout=60):
        self.calls.append(remote_command)
        stdout = self._responses.pop(0) if self._responses else ""
        return subprocess.CompletedProcess(remote_command, 0, stdout=stdout, stderr="")


def test_scan_eadir_parses_du_output():
    ssh = _FakeSSH(["1048576\t/volume1/photo/@eaDir\n2048\t/volume1/photo/sub/@eaDir\n"])

    targets = scan_eadir(ssh, ["/volume1"])

    assert len(targets) == 2
    assert targets[0].path == "/volume1/photo/@eaDir"
    assert targets[0].size_bytes == 1048576
    assert targets[0].action == Action.SSH_DELETE_DIR
    assert targets[0].meta["ssh"] is ssh


def test_scan_recycle_bins_parses_du_output():
    ssh = _FakeSSH(["4096\t/volume1/homes/#recycle\n"])

    targets = scan_recycle_bins(ssh, ["/volume1"])

    assert len(targets) == 1
    assert targets[0].subcategory == "recycle_bin"
    assert targets[0].action == Action.SSH_EMPTY_DIR


def test_scan_ignores_blank_and_malformed_lines():
    ssh = _FakeSSH(["\n   \nnot-a-number\t/volume1/x/@eaDir\n"])

    assert scan_eadir(ssh, ["/volume1"]) == []


def test_scan_temp_aggregates_matching_files_into_one_target():
    ssh = _FakeSSH(["1024\t/volume1/@tmp/upload1.part\n2048\t/volume1/@tmp/upload2.part\n"])

    targets = scan_temp(ssh, ["/volume1"], min_age_days=3)

    assert len(targets) == 1
    assert targets[0].path == "/volume1/@tmp"
    assert targets[0].size_bytes == 3072
    assert targets[0].subcategory == "temp"
    assert targets[0].action == Action.SSH_DELETE_OLD_FILES
    assert targets[0].meta == {"ssh": ssh, "min_age_days": 3}
    assert "mtime +3" in ssh.calls[0]
    assert "/volume1/@tmp" in ssh.calls[0]


def test_scan_temp_returns_nothing_when_no_old_files():
    ssh = _FakeSSH([""])

    assert scan_temp(ssh, ["/volume1"]) == []


def test_scan_all_queries_each_volume_root_for_all_categories():
    ssh = _FakeSSH(["", "", "", "", "", ""])

    scan_all(ssh, ["/volume1", "/volume2"])

    assert len(ssh.calls) == 6
    assert any("/volume1" in call for call in ssh.calls)
    assert any("/volume2" in call for call in ssh.calls)

import subprocess

from cleaner_app.ssh_utils import SSHTarget


def test_base_command_includes_port_and_batch_mode():
    target = SSHTarget(host="nas.local", user="admin")
    cmd = target._base_command()

    assert cmd[0] == "ssh"
    assert "-p" in cmd and cmd[cmd.index("-p") + 1] == "22"
    assert "BatchMode=yes" in cmd
    assert cmd[-1] == "admin@nas.local"


def test_base_command_includes_identity_file_when_set():
    target = SSHTarget(host="nas.local", user="admin", identity_file="/home/me/.ssh/id_ed25519")
    cmd = target._base_command()

    assert "-i" in cmd and cmd[cmd.index("-i") + 1] == "/home/me/.ssh/id_ed25519"


def test_run_invokes_subprocess_with_remote_command(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    target = SSHTarget(host="nas.local", user="admin", port=2222)
    result = target.run("echo hello")

    assert result.stdout == "ok"
    assert captured["cmd"][-1] == "echo hello"
    assert "2222" in captured["cmd"]
    assert captured["kwargs"]["timeout"] == 60

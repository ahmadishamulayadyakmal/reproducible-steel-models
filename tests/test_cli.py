"""Smoke tests for the metalkit CLI."""

import pytest

from metalkit import __version__
from metalkit.cli import main


def test_version_is_exposed():
    assert __version__


def test_help_exits_successfully(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0
    output = capsys.readouterr().out
    assert "usage: metalkit" in output
    assert "metallurgy" in output


def test_info_prints_version_and_description(capsys):
    assert main(["info"]) == 0

    output = capsys.readouterr().out
    assert f"metalkit {__version__}" in output
    assert "Reproducible data and modelling utilities" in output


def test_hash_command_prints_sha256(tmp_path, capsys):
    import hashlib

    target = tmp_path / "data.bin"
    target.write_bytes(b"C01")

    assert main(["hash", str(target)]) == 0

    output = capsys.readouterr().out
    assert hashlib.sha256(b"C01").hexdigest() in output

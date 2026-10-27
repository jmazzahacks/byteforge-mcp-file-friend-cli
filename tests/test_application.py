"""Validate the application boundary and installed console command."""

import json
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path

import pytest
from byteforge_mcp_file_friend_api_python import Client
from byteforge_mcp_file_friend_models import FileReference

from byteforge_mcp_file_friend_cli.cli import main

FILE_ID = "d" * 32


def test_only_cli_distribution_owns_ff() -> None:
    cli = distribution("byteforge-mcp-file-friend-cli")
    sdk = distribution("byteforge-mcp-file-friend-api-python")
    assert [(entry.name, entry.value) for entry in cli.entry_points] == [
        ("ff", "byteforge_mcp_file_friend_cli.cli:main")
    ]
    assert not any(entry.name == "ff" for entry in sdk.entry_points)
    assert not any(str(path).endswith("/cli.py") for path in sdk.files or [])
    result = subprocess.run(
        [str(Path(sys.executable).parent / "ff"), "--help"],
        capture_output=True, text=True, check=False, timeout=5,
    )
    assert result.returncode == 0
    assert "upload" in result.stdout
    assert "download" in result.stdout


def test_upload_delegates_options_and_emits_reference(tmp_path: Path, monkeypatch, capsys) -> None:
    source = tmp_path / "report.pdf"
    reference = {
        "id": FILE_ID,
        "url": f"https://ff.example/f/{FILE_ID}/report.pdf",
        "filename": "report.pdf",
        "size": 123,
        "sha256": "a" * 64,
        "created_at": 1999900000,
        "expires_at": 2000000000,
    }

    def upload(self: Client, path: Path, *, ttl: int, chunk_size: int, restart: bool) -> FileReference:
        assert path == source
        assert ttl == 172800
        assert chunk_size == 32 * 1024
        assert restart is True
        assert self.timeout == 14400
        return FileReference.from_dict(reference)

    monkeypatch.setenv("FF_SERVER_URL", "https://ff.example")
    monkeypatch.setenv("FF_TOKEN", "synthetic-token")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Client, "upload", upload)
    monkeypatch.setattr(sys, "argv", [
        "ff", "upload", str(source), "--ttl", "2d", "--chunk-size", "32K",
        "--restart", "--timeout", "14400",
    ])
    main()
    output = capsys.readouterr()
    assert json.loads(output.out) == FileReference.from_dict(reference).to_dict()
    assert "synthetic-token" not in output.err


def test_download_delegates_to_sdk(tmp_path: Path, monkeypatch, capsys) -> None:
    target = tmp_path / "download.pdf"

    def download(self: Client, reference: str, output: Path) -> Path:
        assert reference == FILE_ID
        assert output == target
        assert self.timeout == 7200
        return output

    monkeypatch.setenv("FF_SERVER_URL", "https://ff.example")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Client, "download", download)
    monkeypatch.setattr(sys, "argv", ["ff", "download", FILE_ID, "-o", str(target), "--timeout", "7200"])
    main()
    assert json.loads(capsys.readouterr().out) == {"path": str(target)}


def test_interrupted_upload_has_resume_guidance(tmp_path: Path, monkeypatch, capsys) -> None:
    def upload(self: Client, *args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setenv("FF_SERVER_URL", "https://ff.example")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Client, "upload", upload)
    monkeypatch.setattr(sys, "argv", ["ff", "upload", str(tmp_path / "file")])
    with pytest.raises(SystemExit) as outcome:
        main()
    assert outcome.value.code == 130
    assert "rerun the command to resume" in capsys.readouterr().err

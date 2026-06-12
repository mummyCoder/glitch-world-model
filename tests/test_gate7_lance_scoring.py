from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_gate7_lance_scoring import main


def _lance_dir(path: Path) -> Path:
    path.mkdir()
    (path / "_versions").mkdir()
    (path / "_transactions").mkdir()
    return path


def test_gate7_dry_run_validates_inputs_without_writing_outputs(tmp_path: Path, capsys):
    checkpoint = tmp_path / "best_weights.pt"
    checkpoint.write_bytes(b"weights")
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    output_dir = tmp_path / "gate7"

    main(
        [
            "--checkpoint",
            str(checkpoint),
            "--config",
            str(config),
            "--normal-lance",
            str(_lance_dir(tmp_path / "normal.lance")),
            "--buggy-lance",
            str(_lance_dir(tmp_path / "buggy.lance")),
            "--output-dir",
            str(output_dir),
            "--expected-sha256",
            "9a129038d9a00aed0cf6a7ea059ca50a813449061ab87848cf1a13eafdf33b2c",
            "--dry-run",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "dry-run"
    assert payload["locked_test_scored"] is False
    assert not output_dir.exists()


def test_gate7_dry_run_rejects_checkpoint_hash_mismatch(tmp_path: Path):
    checkpoint = tmp_path / "best_weights.pt"
    checkpoint.write_bytes(b"weights")
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        main(
            [
                "--checkpoint",
                str(checkpoint),
                "--config",
                str(config),
                "--normal-lance",
                str(_lance_dir(tmp_path / "normal.lance")),
                "--buggy-lance",
                str(_lance_dir(tmp_path / "buggy.lance")),
                "--output-dir",
                str(tmp_path / "gate7"),
                "--expected-sha256",
                "wrong",
                "--dry-run",
            ]
        )


def test_gate7_allows_nonlocked_name_but_rejects_locked_test_name(tmp_path: Path, capsys):
    checkpoint = tmp_path / "best_weights.pt"
    checkpoint.write_bytes(b"weights")
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    normal = _lance_dir(tmp_path / "normal.lance")
    nonlocked = _lance_dir(tmp_path / "tempglitch_nonlocked_buggy.lance")
    common = [
        "--checkpoint",
        str(checkpoint),
        "--config",
        str(config),
        "--normal-lance",
        str(normal),
        "--output-dir",
        str(tmp_path / "gate7"),
        "--expected-sha256",
        "9a129038d9a00aed0cf6a7ea059ca50a813449061ab87848cf1a13eafdf33b2c",
        "--dry-run",
    ]

    main([*common, "--buggy-lance", str(nonlocked)])
    assert json.loads(capsys.readouterr().out)["status"] == "dry-run"

    locked = _lance_dir(tmp_path / "locked_test.lance")
    with pytest.raises(ValueError, match="locked"):
        main([*common, "--buggy-lance", str(locked)])

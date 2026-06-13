import json
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import glitch_detection.lewm_gpu_profile_automation as automation
from glitch_detection.lewm_gpu_profile_automation import (
    ProfileAttemptRunner,
    ProfileAutomationConfig,
    run_profile_attempt_ladder,
    validate_live_launch_contract,
)


def _config(tmp_path: Path) -> ProfileAutomationConfig:
    return ProfileAutomationConfig(
        repo_root=Path(__file__).resolve().parents[1],
        lance_root=tmp_path / "datasets",
        source_audit=tmp_path / "source_audit.json",
        run_root=tmp_path / "run",
        dataset_slug="huynhdieuthanh/lewm-profile-private",
    )


def test_oom_coordinator_tries_8_6_4_and_preserves_attempts(tmp_path: Path):
    config = _config(tmp_path)

    def attempt(batch_size: int):
        root = tmp_path / f"attempt-{batch_size}"
        root.mkdir()
        if batch_size in {8, 6}:
            return {
                "batch_size": batch_size,
                "fingerprint": f"fp-{batch_size}",
                "attempt_root": str(root),
                "status": "failed",
                "failure": {"classification": "cuda_oom"},
            }
        return {
            "batch_size": batch_size,
            "fingerprint": f"fp-{batch_size}",
            "attempt_root": str(root),
            "artifact_root": str(root),
            "status": "success",
        }

    result = run_profile_attempt_ladder(config, attempt_runner=attempt)
    assert result["attempted_batch_sizes"] == [8, 6, 4]
    assert len({row["fingerprint"] for row in result["attempts"]}) == 3
    assert json.loads((config.run_root / "retry_history.json").read_text())["attempts"]


def test_non_oom_failure_does_not_advance_ladder(tmp_path: Path):
    config = _config(tmp_path)
    result = run_profile_attempt_ladder(
        config,
        attempt_runner=lambda batch: {
            "batch_size": batch,
            "fingerprint": "fp",
            "attempt_root": str(tmp_path / "attempt"),
            "status": "failed",
            "failure": {
                "classification": "runtime_error",
                "message": "An attempt has been made to start a new process before the current "
                "process has finished its bootstrapping phase",
            },
        },
    )
    assert result["attempted_batch_sizes"] == [8]
    failure = result["attempts"][0]["failure"]
    assert failure["bucket"] == "dataloader_spawn"
    assert failure["allowed_action"] == "stop_and_fix"


def test_successful_kernel_with_invalid_artifacts_is_recorded_as_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    config = replace(_config(tmp_path), live=True, poll_interval_seconds=0)
    artifact_root = tmp_path / "artifact"
    artifact_root.mkdir()
    (artifact_root / "profile_metadata.json").write_text("{}", encoding="utf-8")

    def fake_package(*args, dry_run: bool, **kwargs):
        if not dry_run:
            (args[2] / "kernel").mkdir(parents=True)
            (args[2] / "dataset").mkdir(parents=True)
        return {
            "profile_fingerprint": "fp",
            "kernel_inventory_sha256": "kernel-sha",
        }

    monkeypatch.setattr(automation, "prepare_profile_kaggle_package", fake_package)
    monkeypatch.setattr(automation, "validate_profile_kaggle_package", lambda _root: {})
    runner = ProfileAttemptRunner(config)
    monkeypatch.setattr(
        runner,
        "preflight",
        lambda: {"git_sha": "sha", "branch": "main"},
    )
    monkeypatch.setattr(runner, "_dataset_upload", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "_wait_dataset", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "_download", lambda *_args, **_kwargs: artifact_root)
    monkeypatch.setattr(
        runner,
        "_run",
        lambda _root, step, _command: SimpleNamespace(
            stdout="complete" if step == "kernel_poll" else ""
        ),
    )

    result = runner.run_attempt(8)

    assert result["status"] == "failed"
    assert result["failure"]["classification"] == "artifact_contract_error"
    assert result["failure"]["error_type"] == "FileNotFoundError"


def _git_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "profile.py").write_text("READY = True\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    return repo, sha


def _live_config(tmp_path: Path) -> ProfileAutomationConfig:
    repo, sha = _git_repo(tmp_path)
    receipt = tmp_path / "parity_receipt.json"
    receipt.write_text(json.dumps({"pass": True, "git_sha": sha}), encoding="utf-8")
    return replace(_config(tmp_path), repo_root=repo, live=True, parity_receipt=receipt)


def test_live_contract_accepts_clean_matching_parity_receipt(tmp_path: Path):
    assert validate_live_launch_contract(_live_config(tmp_path))["required"] is True


def test_live_contract_blocks_missing_or_mismatched_parity_receipt(tmp_path: Path):
    config = _live_config(tmp_path)
    with pytest.raises(FileNotFoundError, match="parity receipt"):
        validate_live_launch_contract(replace(config, parity_receipt=tmp_path / "missing.json"))
    config.parity_receipt.write_text(
        json.dumps({"pass": True, "git_sha": "other"}), encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="does not match HEAD"):
        validate_live_launch_contract(config)


def test_live_contract_blocks_dirty_profile_source_and_existing_run_root(tmp_path: Path):
    config = _live_config(tmp_path)
    (config.repo_root / "src" / "profile.py").write_text("READY = False\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="clean profile implementation"):
        validate_live_launch_contract(config)
    subprocess.run(["git", "checkout", "--", "src/profile.py"], cwd=config.repo_root, check=True)
    config.run_root.mkdir()
    with pytest.raises(FileExistsError, match="run-root already exists"):
        validate_live_launch_contract(config)

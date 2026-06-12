import json
from pathlib import Path

from glitch_detection.lewm_gpu_profile_automation import (
    ProfileAutomationConfig,
    run_profile_attempt_ladder,
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
            "failure": {"classification": "runtime_error"},
        },
    )
    assert result["attempted_batch_sizes"] == [8]

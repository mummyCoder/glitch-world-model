import json
from pathlib import Path

import pytest

from glitch_detection.kaggle_automation import FingerprintBuilder
from glitch_detection.lewm_gpu_profile import (
    LeWMGPUProfileConfig,
    build_checkpoint_payload,
    build_dataset_manifest,
    build_profile_fingerprint,
    run_exact_updates,
    validate_lewm_gpu_profile_artifacts,
    verify_reloaded_checkpoint,
)


def test_profile_config_freezes_engineering_only_contract():
    config = LeWMGPUProfileConfig(batch_size=8)
    assert config.optimizer_updates == 500
    assert config.validation_batches == 8
    assert config.num_workers == 0
    assert config.seed == 42
    assert config.validation_only is True
    assert config.locked_test_materialized is False


def test_dataset_manifest_is_canonical_and_content_sensitive(tmp_path: Path):
    train, validation = tmp_path / "train.lance", tmp_path / "validation.lance"
    train.mkdir()
    validation.mkdir()
    (train / "part.bin").write_bytes(b"train")
    (validation / "part.bin").write_bytes(b"validation")
    first = build_dataset_manifest(train, validation)
    (train / "part.bin").write_bytes(b"changed")
    second = build_dataset_manifest(train, validation)
    assert first["dataset_manifest_hash"] != second["dataset_manifest_hash"]
    assert [row["split"] for row in first["files"]] == ["train_normal", "validation_normal"]


@pytest.mark.parametrize(
    "change",
    [
        {"git_sha": "other"},
        {"dataset_manifest_hash": "other"},
        {"config_hash": "other"},
        {"batch_size": 6},
        {"amp": True},
    ],
)
def test_profile_fingerprint_changes_for_every_immutable_field(change):
    base = {
        "git_sha": "abc",
        "dataset_manifest_hash": "dataset",
        "train_dataset_hash": "train",
        "validation_dataset_hash": "validation",
        "config_hash": "config",
        "batch_size": 8,
        "amp": False,
    }
    assert build_profile_fingerprint(base) != build_profile_fingerprint({**base, **change})


def test_exact_update_loop_stops_at_500_without_overrun():
    calls = []
    result = run_exact_updates(
        target_updates=500,
        train_step=lambda update: calls.append(update) or {"loss": 1.0 / update},
    )
    assert calls == list(range(1, 501))
    assert result["updates_completed"] == 500


def test_exact_update_loop_rejects_non_finite_loss():
    with pytest.raises(ValueError, match="non-finite"):
        run_exact_updates(target_updates=500, train_step=lambda _update: {"loss": float("nan")})


def test_checkpoint_contract_verifies_optional_scheduler_and_step():
    checkpoint = build_checkpoint_payload(
        model_state={"weight": 1},
        optimizer_state={"state": 1},
        scheduler_state=None,
        global_step=500,
        config_hash="config",
        dataset_hashes={"train": "train", "validation": "validation"},
    )
    result = verify_reloaded_checkpoint(
        checkpoint,
        expected_step=500,
        expected_config_hash="config",
        expected_dataset_hashes={"train": "train", "validation": "validation"},
    )
    assert result["scheduler"] == {"present": False, "reload_verified": True}


def _write_valid_artifacts(root: Path) -> None:
    checkpoint = root / "checkpoint.pt"
    checkpoint.write_bytes(b"checkpoint")
    checkpoint_hash = FingerprintBuilder.sha256_file(checkpoint)
    metadata = {
        "evidence_class": "engineering-profile-only",
        "fingerprint": "fingerprint",
        "device": "cuda",
        "updates_completed": 500,
        "validation_batches_completed": 8,
        "wall_clock_runtime_seconds": 10.0,
        "updates_per_second": 50.0,
        "peak_vram_bytes": 100,
        "average_vram_bytes": 80,
        "checkpoint_reload": {
            "weights_reload_verified": True,
            "optimizer_reload_verified": True,
            "scheduler": {"present": False, "reload_verified": True},
            "reloaded_global_step": 500,
        },
    }
    files = {
        "PROFILE_REPORT.md": "engineering profile only\n",
        "profile_metadata.json": json.dumps(metadata),
        "environment_snapshot.json": json.dumps({"cuda_available": True}),
        "checkpoint_hashes.json": json.dumps({"checkpoint_sha256": checkpoint_hash}),
        "retry_history.json": json.dumps({"attempts": []}),
        "profile.log": "complete\n",
    }
    for name, text in files.items():
        (root / name).write_text(text, encoding="utf-8")
    manifest = {
        "files": {
            name: {"sha256": FingerprintBuilder.sha256_file(root / name)}
            for name in (*files, "checkpoint.pt")
        }
    }
    (root / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_strict_profile_validator_accepts_engineering_artifacts(tmp_path: Path):
    _write_valid_artifacts(tmp_path)
    assert validate_lewm_gpu_profile_artifacts(tmp_path)["status"] == "lewm_gpu_profile_validated"


def test_strict_profile_validator_rejects_wrong_update_count(tmp_path: Path):
    _write_valid_artifacts(tmp_path)
    path = tmp_path / "profile_metadata.json"
    metadata = json.loads(path.read_text())
    metadata["updates_completed"] = 499
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="exactly 500"):
        validate_lewm_gpu_profile_artifacts(tmp_path)

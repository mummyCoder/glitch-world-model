import json
from pathlib import Path

import pytest

from glitch_detection.lewm_gate6 import (
    GATE6_REQUIRED_OUTPUTS,
    Gate6KaggleConfig,
    prepare_gate6_kaggle_package,
    render_gate6_kernel,
    validate_gate6_artifacts,
)


def _config() -> Gate6KaggleConfig:
    return Gate6KaggleConfig(
        dataset_slug="huynhdieuthanh/lewm-tempglitch-gate6-pilot",
        kernel_slug="huynhdieuthanh/lewm-gate6-pilot-v1",
        dataset_id="tempglitch-lewm-gate6",
        train_dataset_name="train.lance",
        validation_dataset_name="validation.lance",
        buggy_probe_dataset_name="buggy.lance",
    )


def test_gate6_package_requires_three_datasets_and_stays_locked(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for name in ("train.lance", "validation.lance", "buggy.lance"):
        (source / name).mkdir()
    summary = prepare_gate6_kaggle_package(source, tmp_path / "package", _config(), dry_run=True)
    kernel = render_gate6_kernel(_config())

    assert summary["locked_test_included"] is False
    assert "normal_only_training" in kernel
    assert "score_lance_probe" in kernel
    assert "Locked-test execution is forbidden" in kernel
    assert "shutil.unpack_archive" in kernel
    assert "glitch_detection_src.zip" in kernel


def test_gate6_materialized_package_archives_lance_directories(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for name in ("train.lance", "validation.lance", "buggy.lance"):
        dataset = source / name
        dataset.mkdir()
        (dataset / "data.bin").write_bytes(b"lance")

    package = tmp_path / "package"
    prepare_gate6_kaggle_package(source, package, _config(), dry_run=False)

    assert (package / "dataset" / "train.lance.zip").is_file()
    assert not (package / "dataset" / "train.lance").exists()
    assert (package / "kernel" / "glitch_detection_src.zip").is_file()


def _write_valid_artifacts(root: Path) -> None:
    for name in GATE6_REQUIRED_OUTPUTS:
        (root / name).write_text("{}\n", encoding="utf-8")
    (root / "environment.json").write_text('{"cuda_available":true}\n', encoding="utf-8")
    (root / "training_metadata.json").write_text(
        '{"device":"cuda","completed_epoch":1,"checkpoint_sha256":"hash",'
        '"locked_test_materialized":false,"locked_test_scored":false}\n',
        encoding="utf-8",
    )
    normal = '"normal_only_training":true,"normal_only_validation":true'
    (root / "dataset_metadata.json").write_text("{" + normal + "}\n", encoding="utf-8")
    (root / "protocol_audit.json").write_text(
        "{" + normal + ',"locked_test_materialized":false,"locked_test_scored":false}\n',
        encoding="utf-8",
    )
    (root / "loss_history.json").write_text(
        '[{"epoch":1,"train":[{"loss":1.0}],"validation":[{"loss":0.9}]}]\n',
        encoding="utf-8",
    )
    (root / "collapse_diagnostics.json").write_text(
        '{"finite":true,"latent_variance_mean":0.2,"latent_variance_min":0.1}\n',
        encoding="utf-8",
    )
    (root / "checkpoint_reload.json").write_text(
        '{"checkpoint_reload_verified":true,"best_weights_sha256":"best","best_epoch":1}\n',
        encoding="utf-8",
    )
    (root / "encoding_proof.json").write_text(
        '{"normal_validation":{"finite":true,"surprise_mean":0.2},'
        '"nonlocked_buggy_validation":{"finite":true,"surprise_mean":0.3}}\n',
        encoding="utf-8",
    )
    (root / "checkpoint.sha256").write_text("hash\n", encoding="utf-8")


def test_gate6_validator_accepts_strict_artifacts(tmp_path: Path):
    _write_valid_artifacts(tmp_path)

    result = validate_gate6_artifacts(tmp_path)

    assert result["status"] == "gate6_passed"
    assert result["locked_test_scored"] is False


def test_gate6_validator_rejects_buggy_training(tmp_path: Path):
    _write_valid_artifacts(tmp_path)
    metadata = json.loads((tmp_path / "dataset_metadata.json").read_text())
    metadata["normal_only_training"] = False
    (tmp_path / "dataset_metadata.json").write_text(json.dumps(metadata))

    with pytest.raises(ValueError, match="not normal-only"):
        validate_gate6_artifacts(tmp_path)

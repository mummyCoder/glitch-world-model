import csv
import json
from pathlib import Path

import pytest

from scripts.ingest_phase6e_kaggle_artifacts import ingest_phase6e_kaggle_artifacts


def _write_artifacts(
    root: Path,
    *,
    device: str = "cuda",
    score_values: list[str] | None = None,
    test_scored: bool = False,
) -> None:
    root.mkdir(parents=True)
    (root / "protocol_audit.json").write_text(
        json.dumps(
            {
                "leakage_audit": {"cross_split_group_count": 0},
                "test_materialized": False,
                "test_scored": test_scored,
                "validation_clip_count": 2,
            }
        ),
        encoding="utf-8",
    )
    (root / "training_metadata.json").write_text(
        json.dumps({"device": device, "epoch_losses": [0.2, 0.1]}),
        encoding="utf-8",
    )
    (root / "phase6e_summary.json").write_text(
        json.dumps({"test_materialized": False, "test_scored": test_scored}),
        encoding="utf-8",
    )
    values = score_values or ["0.1", "0.2"]
    with (root / "validation_scores.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["clip_id", "source", "clip_dir", "start_frame", "end_frame", "score"],
        )
        writer.writeheader()
        for index, value in enumerate(values):
            writer.writerow(
                {
                    "clip_id": f"clip_{index}",
                    "source": f"source_{index}",
                    "clip_dir": f"/kaggle/input/clips/clip_{index}",
                    "start_frame": 0,
                    "end_frame": 15,
                    "score": value,
                }
            )


def test_ingest_rejects_missing_required_artifacts(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="protocol_audit.json"):
        ingest_phase6e_kaggle_artifacts(
            artifact_root=tmp_path / "missing",
            output_root=tmp_path / "output",
            expected_validation_rows=2,
        )


def test_ingest_rejects_cpu_metadata_in_strict_cuda_mode(tmp_path: Path):
    artifact_root = tmp_path / "artifacts"
    _write_artifacts(artifact_root, device="cpu")

    with pytest.raises(ValueError, match="CUDA"):
        ingest_phase6e_kaggle_artifacts(
            artifact_root=artifact_root,
            output_root=tmp_path / "output",
            expected_validation_rows=2,
        )


def test_ingest_rejects_nan_scores(tmp_path: Path):
    artifact_root = tmp_path / "artifacts"
    _write_artifacts(artifact_root, score_values=["0.1", "nan"])

    with pytest.raises(ValueError, match="finite"):
        ingest_phase6e_kaggle_artifacts(
            artifact_root=artifact_root,
            output_root=tmp_path / "output",
            expected_validation_rows=2,
        )


def test_ingest_rejects_any_test_scoring_flag(tmp_path: Path):
    artifact_root = tmp_path / "artifacts"
    _write_artifacts(artifact_root, test_scored=True)

    with pytest.raises(ValueError, match="test_scored"):
        ingest_phase6e_kaggle_artifacts(
            artifact_root=artifact_root,
            output_root=tmp_path / "output",
            expected_validation_rows=2,
        )


def test_ingest_writes_validation_report_for_valid_cuda_artifacts(tmp_path: Path):
    artifact_root = tmp_path / "artifacts"
    output_root = tmp_path / "output"
    _write_artifacts(artifact_root)

    summary = ingest_phase6e_kaggle_artifacts(
        artifact_root=artifact_root,
        output_root=output_root,
        expected_validation_rows=2,
    )

    assert summary["status"] == "artifact validation complete"
    assert summary["device"] == "cuda"
    assert summary["validation_row_count"] == 2
    assert summary["nan_or_non_finite_score_count"] == 0
    assert summary["test_scored"] is False
    assert (output_root / "artifact_validation_summary.json").is_file()
    assert (output_root / "artifact_validation_report.md").is_file()


def test_ingest_accepts_json_artifacts_with_utf8_bom(tmp_path: Path):
    artifact_root = tmp_path / "artifacts"
    _write_artifacts(artifact_root)
    protocol_text = (artifact_root / "protocol_audit.json").read_text(encoding="utf-8")
    (artifact_root / "protocol_audit.json").write_text(protocol_text, encoding="utf-8-sig")

    summary = ingest_phase6e_kaggle_artifacts(
        artifact_root=artifact_root,
        output_root=tmp_path / "output",
        expected_validation_rows=2,
    )

    assert summary["status"] == "artifact validation complete"

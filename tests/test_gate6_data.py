import csv
from pathlib import Path

import pytest

from glitch_detection.gate6_data import audit_gate6_source, select_tempglitch_rows


def _row(source: str, split: str, label: str, pair: str) -> dict[str, str]:
    return {
        "source": source,
        "episode_id": source,
        "split": split,
        "label": label,
        "pair_id": pair,
        "category": "Velocity",
        "materialize": "True",
    }


def test_selection_filters_labels_and_is_deterministic():
    metadata = {source: {"source": source} for source in ("a", "b", "c")}
    split = {
        "a": _row("a", "validation", "Normal", "p1"),
        "b": _row("b", "validation", "Buggy", "p2"),
        "c": _row("c", "validation", "Normal", "p3"),
    }

    first = select_tempglitch_rows(
        metadata,
        split,
        partition="validation",
        label_filter="Normal",
        max_episodes=1,
        seed=42,
    )
    second = select_tempglitch_rows(
        metadata,
        split,
        partition="validation",
        label_filter="Normal",
        max_episodes=1,
        seed=42,
    )

    assert first == second
    assert first[0]["label"] == "Normal"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_gate6_audit_rejects_pair_leakage(tmp_path: Path):
    video_root = tmp_path / "videos"
    video_root.mkdir()
    metadata_rows = []
    split_rows = []
    for source, partition, label, pair in [
        ("train", "train", "Normal", "shared"),
        ("normal", "validation", "Normal", "shared"),
        ("buggy", "validation", "Buggy", "bug-pair"),
    ]:
        (video_root / f"{source}.mp4").write_bytes(b"video")
        metadata_rows.append({"source": source, "local_video_path": f"{source}.mp4"})
        split_rows.append(_row(source, partition, label, pair))
    metadata_path = tmp_path / "metadata.csv"
    split_path = tmp_path / "split.csv"
    _write_csv(metadata_path, metadata_rows)
    _write_csv(split_path, split_rows)

    with pytest.raises(ValueError, match="leakage"):
        audit_gate6_source(
            metadata_path,
            split_path,
            video_root,
            train_count=1,
            validation_count=1,
            buggy_probe_count=1,
        )


def test_gate6_audit_reports_locked_test_false(tmp_path: Path):
    video_root = tmp_path / "videos"
    video_root.mkdir()
    metadata_rows = []
    split_rows = []
    for source, partition, label, pair in [
        ("train", "train", "Normal", "train-pair"),
        ("normal", "validation", "Normal", "normal-pair"),
        ("buggy", "validation", "Buggy", "bug-pair"),
    ]:
        (video_root / f"{source}.mp4").write_bytes(b"video")
        metadata_rows.append({"source": source, "local_video_path": f"{source}.mp4"})
        split_rows.append(_row(source, partition, label, pair))
    metadata_path = tmp_path / "metadata.csv"
    split_path = tmp_path / "split.csv"
    _write_csv(metadata_path, metadata_rows)
    _write_csv(split_path, split_rows)

    result = audit_gate6_source(
        metadata_path,
        split_path,
        video_root,
        train_count=1,
        validation_count=1,
        buggy_probe_count=1,
    )

    assert result["normal_only_training"] is True
    assert result["normal_only_validation"] is True
    assert result["locked_test_materialized"] is False

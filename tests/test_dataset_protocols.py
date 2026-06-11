import json
from pathlib import Path

import pytest

from glitch_detection.dataset_protocols import (
    audit_frozen_split,
    freeze_tempglitch_split,
    freeze_wob_split,
    write_frozen_split,
)


def _tempglitch_rows(pair_count: int = 20) -> list[dict[str, str]]:
    return [
        {
            "source": f"Godot_{category}_{label}_{index}",
            "episode_id": f"Godot_{category}_{label}_{index}",
            "pair_id": f"{category}/pair-index:{index}",
            "category": category,
            "label": label,
        }
        for category in ["Blinking", "Velocity Bug"]
        for index in range(pair_count)
        for label in ["Buggy", "Normal"]
    ]


def test_tempglitch_freeze_is_normal_only_and_keeps_exposed_groups_out_of_test():
    exposed = {"Blinking/pair-index:0", "Velocity Bug/pair-index:1"}

    records = freeze_tempglitch_split(_tempglitch_rows(), exposed_groups=exposed, seed=42)
    audit = audit_frozen_split(records, exposed_groups=exposed)

    assert records == freeze_tempglitch_split(_tempglitch_rows(), exposed_groups=exposed, seed=42)
    assert all(record.label == "Normal" for record in records if record.split == "train")
    assert all(not record.materialize for record in records if record.split == "test")
    assert audit["cross_split_group_count"] == 0
    assert audit["exposed_test_group_count"] == 0
    assert audit["non_normal_train_count"] == 0
    assert audit["materialized_test_count"] == 0
    assert audit["locked_test_materialized"] is False
    assert audit["locked_test_scored"] is False


def test_wob_freeze_separates_normal_training_from_bug_validation_and_test():
    normal = [
        {
            "source": f"NORMAL-TRAIN/ep-{index:04d}/ep-{index:04d}.tar",
            "episode_id": f"normal-{index:04d}",
            "category": "Normal",
            "label": "Normal",
        }
        for index in range(20)
    ]
    bugs = [
        {
            "source": f"TEST/{category}/ep-{index:04d}/ep-{index:04d}.tar",
            "episode_id": f"{category}-{index:04d}",
            "category": category,
            "label": "Buggy",
        }
        for category in ["BlackScreen", "BoundaryHole"]
        for index in range(20)
    ]

    records = freeze_wob_split(normal, bugs, seed=42)
    audit = audit_frozen_split(records)

    assert {record.split for record in records if record.label == "Normal"} == {
        "train",
        "validation",
    }
    assert {record.split for record in records if record.label == "Buggy"} == {
        "validation",
        "test",
    }
    assert all(not record.materialize for record in records if record.split == "test")
    assert audit["cross_split_group_count"] == 0
    assert audit["non_normal_train_count"] == 0
    assert audit["materialized_test_count"] == 0


def test_frozen_split_rejects_duplicate_sources_and_writes_hashes(tmp_path: Path):
    rows = _tempglitch_rows()
    records = freeze_tempglitch_split(rows, seed=42)
    split_path, audit_path, provenance_path = write_frozen_split(
        tmp_path / "split.csv",
        records,
        seed=42,
        provenance={"dataset_revision": "abc123", "source_url": "https://example.test"},
    )

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert audit["split_sha256"] == provenance["split_sha256"]
    assert provenance["dataset_revision"] == "abc123"
    assert len(provenance["split_sha256"]) == 64

    duplicate = [records[0], records[0]]
    with pytest.raises(ValueError, match="duplicate"):
        write_frozen_split(tmp_path / "duplicate.csv", duplicate, seed=42, provenance={})

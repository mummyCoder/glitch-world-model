import json
from pathlib import Path

from glitch_detection.splits import (
    assign_grouped_video_splits,
    validate_no_group_leakage,
    write_grouped_split_csv,
)


def _paired_metadata(pair_count: int = 10) -> list[dict[str, str]]:
    return [
        {
            "source": f"Godot_{category}_{label}_{index}",
            "category": category,
            "public_label": label,
        }
        for category in ["Blinking", "Velocity"]
        for index in range(pair_count)
        for label in ["Buggy", "Normal"]
    ]


def test_grouped_split_keeps_suspected_pairs_together_and_is_deterministic():
    first = assign_grouped_video_splits(_paired_metadata(), seed=42)
    second = assign_grouped_video_splits(_paired_metadata(), seed=42)

    assert first == second
    assert validate_no_group_leakage(first)["cross_split_group_count"] == 0
    assert {row.split for row in first} == {"train", "validation", "test"}


def test_grouped_split_changes_with_seed():
    first = assign_grouped_video_splits(_paired_metadata(), seed=42)
    second = assign_grouped_video_splits(_paired_metadata(), seed=43)

    assert first != second


def test_write_grouped_split_csv_records_grouping_metadata(tmp_path: Path):
    records = assign_grouped_video_splits(_paired_metadata(), seed=42)

    split_path, metadata_path = write_grouped_split_csv(tmp_path / "split.csv", records, seed=42)

    assert split_path.read_text(encoding="utf-8").splitlines()[0] == (
        "source,category,label,split,pair_id_heuristic"
    )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["seed"] == 42
    assert metadata["grouping_mode"] == "pair_id_heuristic"
    assert metadata["group_count"] == 20
    assert metadata["suspected_pair_count"] == 20
    assert metadata["cross_split_group_count"] == 0

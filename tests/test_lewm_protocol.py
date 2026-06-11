from pathlib import Path

from glitch_detection.lewm_protocol import (
    assign_hashed_group_splits,
    audit_lewm_splits,
    write_lewm_split,
)


def _rows() -> list[dict[str, str]]:
    return [
        {
            "source": f"source-{group}-{label}",
            "episode_id": f"episode-{group}-{label}",
            "pair_id": f"pair-{group}",
            "category": "velocity",
            "label": label,
            "action_mode": "zero_action",
        }
        for group in range(30)
        for label in ("Normal", "Buggy")
    ]


def test_hashed_splits_are_deterministic_grouped_and_keep_exposed_out_of_test(tmp_path: Path):
    exposed = {"pair-1", "pair-2"}
    first = assign_hashed_group_splits(
        _rows(), dataset_id="tempglitch", seed=42, exposed_groups=exposed
    )
    second = assign_hashed_group_splits(
        _rows(), dataset_id="tempglitch", seed=42, exposed_groups=exposed
    )

    assert first == second
    audit = audit_lewm_splits(first, exposed_groups=exposed)
    assert audit["cross_split_group_count"] == 0
    assert audit["exposed_test_group_count"] == 0
    assert set(audit["split_counts"]) == {"train", "validation", "test"}

    split_path, audit_path = write_lewm_split(
        tmp_path / "split.csv", first, seed=42, exposed_groups=exposed
    )
    assert split_path.is_file()
    assert audit_path.is_file()

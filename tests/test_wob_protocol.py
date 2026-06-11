import io
import tarfile
from pathlib import Path

import numpy as np
import pytest

from glitch_detection.lewm_data import episode_from_wob_tar
from glitch_detection.wob_protocol import inspect_wob_episode_tar, parse_wob_inventory


def _write_episode(path: Path, indices: list[int]) -> None:
    with tarfile.open(path, "w") as archive:
        for index in indices:
            payload = io.BytesIO()
            np.savez(
                payload,
                state=np.full((3, 8, 8), index, dtype=np.float32),
                action=np.array(index % 4, dtype=np.int64),
                reward=np.array(0.0, dtype=np.float32),
                done=np.array(index == indices[-1], dtype=np.uint8),
            )
            data = payload.getvalue()
            info = tarfile.TarInfo(f"{index:08d}.npz")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def test_inspect_wob_episode_tar_verifies_numeric_schema_and_contiguous_steps(tmp_path: Path):
    episode = tmp_path / "episode.tar"
    _write_episode(episode, [0, 1, 2])

    audit = inspect_wob_episode_tar(episode, minimum_steps=3)

    assert audit["step_count"] == 3
    assert audit["contiguous_step_indices"] is True
    assert audit["state_shape"] == [3, 8, 8]
    assert audit["action_shape"] == []
    assert audit["action_values"] == [0, 1, 2]
    assert audit["required_numeric_schema_valid"] is True
    assert audit["semantic_action_synchronization_verified"] is False

    converted = episode_from_wob_tar(
        episode,
        dataset_id="wob",
        source="episode.tar",
        episode_id="normal/ep-0000",
        category="Normal",
        label="Normal",
        split="train",
        pair_id="normal/ep-0000",
    )
    assert converted.action.shape == (3, 4)
    assert converted.action.tolist() == [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ]
    assert converted.pixels[0].shape == (8, 8, 3)


def test_inspect_wob_episode_tar_rejects_short_or_non_contiguous_episode(tmp_path: Path):
    episode = tmp_path / "episode.tar"
    _write_episode(episode, [0, 2])

    with pytest.raises(ValueError, match="shorter"):
        inspect_wob_episode_tar(episode, minimum_steps=3)
    with pytest.raises(ValueError, match="not contiguous"):
        inspect_wob_episode_tar(episode, minimum_steps=2)


def test_parse_wob_inventory_excludes_small_normal_duplicate_set():
    rows = [
        {"name": "NORMAL-TRAIN/ep-0000/ep-0000.tar", "size": "10"},
        {"name": "NORMAL-TRAIN-SMALL/ep-0000/ep-0000.tar", "size": "10"},
        {"name": "TEST/BlackScreen/ep-0000/ep-0000.tar", "size": "12"},
    ]

    normal, bugs, audit = parse_wob_inventory(rows)

    assert normal == [
        {
            "source": "NORMAL-TRAIN/ep-0000/ep-0000.tar",
            "episode_id": "normal/ep-0000",
            "category": "Normal",
            "label": "Normal",
            "size_bytes": "10",
        }
    ]
    assert bugs[0]["episode_id"] == "BlackScreen/ep-0000"
    assert audit["excluded_small_normal_count"] == 1

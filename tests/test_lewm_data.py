from pathlib import Path

import numpy as np
from PIL import Image

from glitch_detection.lewm_data import LeWMEpisode, episode_from_clip
from glitch_detection.manifest import ClipRecord


def test_zero_action_episode_from_clip_preserves_steps(tmp_path: Path):
    clip_dir = tmp_path / "clip"
    clip_dir.mkdir()
    for index in range(4):
        Image.new("RGB", (8, 8), (index, index, index)).save(clip_dir / f"{index:06d}.png")
    record = ClipRecord("clip-1", "source-1", str(clip_dir), 0, 3, 4, 30.0)

    episode = episode_from_clip(
        record,
        dataset_id="tempglitch",
        category="Velocity",
        label="Normal",
        split="train",
        pair_id="pair-1",
    )

    assert isinstance(episode, LeWMEpisode)
    assert len(episode.pixels) == 4
    assert episode.action.shape == (4, 1)
    assert np.all(episode.action == 0)
    assert episode.writer_payload()["action_mode"] == ["zero_action"] * 4


def test_real_action_episode_rejects_length_mismatch(tmp_path: Path):
    pixels = [np.zeros((8, 8, 3), dtype=np.uint8)] * 4
    try:
        LeWMEpisode(
            "wob",
            "source",
            "episode",
            pixels,
            np.zeros((3, 2), dtype=np.float32),
            "Buggy",
            "bug",
            "validation",
            "episode",
            "real",
        )
    except ValueError as exc:
        assert "identical lengths" in str(exc)
    else:
        raise AssertionError("Expected action length mismatch to fail.")

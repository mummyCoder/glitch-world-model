from pathlib import Path

from PIL import Image

from glitch_detection.frame_diff import score_clip


def _write_clip(path: Path, values: list[int]) -> None:
    path.mkdir(parents=True)
    for index, value in enumerate(values):
        Image.new("RGB", (8, 8), color=(value, value, value)).save(path / f"{index:06d}.png")


def test_changing_clip_scores_higher_than_static_clip(tmp_path: Path):
    static_clip = tmp_path / "static"
    changing_clip = tmp_path / "changing"
    _write_clip(static_clip, [30, 30, 30, 30])
    _write_clip(changing_clip, [0, 40, 80, 120])

    assert score_clip(changing_clip) > score_clip(static_clip)
    assert score_clip(static_clip) == 0.0

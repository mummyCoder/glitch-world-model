from pathlib import Path

from PIL import Image

from glitch_detection.feature_distance import clip_feature, score_records
from glitch_detection.manifest import ClipRecord


def _write_clip(path: Path, colors: list[tuple[int, int, int]]) -> None:
    path.mkdir(parents=True)
    for index, color in enumerate(colors):
        Image.new("RGB", (16, 16), color=color).save(path / f"{index:06d}.png")


def test_feature_distance_scores_glitch_farther_from_normal(tmp_path: Path):
    normal_clip = tmp_path / "normal"
    glitch_clip = tmp_path / "glitch"
    _write_clip(normal_clip, [(30, 40, 50), (32, 42, 52), (31, 41, 51)])
    _write_clip(glitch_clip, [(220, 30, 30), (230, 20, 20), (225, 25, 25)])

    records = [
        ClipRecord("normal", "demo", str(normal_clip), 0, 2, 3, 30.0),
        ClipRecord("glitch", "demo", str(glitch_clip), 3, 5, 3, 30.0),
    ]
    labels = [0, 1]
    scores = score_records(records, labels)

    assert scores["glitch"] > scores["normal"]
    assert len(clip_feature(normal_clip)) == 6

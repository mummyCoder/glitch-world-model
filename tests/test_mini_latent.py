from pathlib import Path

from PIL import Image

from glitch_detection.manifest import ClipRecord
from glitch_detection.mini_latent import score_records


def _write_clip(path: Path, values: list[int]) -> None:
    path.mkdir(parents=True)
    for index, value in enumerate(values):
        Image.new("RGB", (16, 16), color=(value, value, value)).save(path / f"{index:06d}.png")


def test_mini_latent_scores_transition_glitch_higher(tmp_path: Path):
    normal_a = tmp_path / "normal_a"
    normal_b = tmp_path / "normal_b"
    glitch = tmp_path / "glitch"
    _write_clip(normal_a, [20, 25, 30, 35, 40])
    _write_clip(normal_b, [30, 35, 40, 45, 50])
    _write_clip(glitch, [20, 25, 240, 25, 20])

    records = [
        ClipRecord("normal_a", "demo", str(normal_a), 0, 4, 5, 30.0),
        ClipRecord("normal_b", "demo", str(normal_b), 5, 9, 5, 30.0),
        ClipRecord("glitch", "demo", str(glitch), 10, 14, 5, 30.0),
    ]
    scores = score_records(records, labels=[0, 0, 1], latent_dim=2, image_size=16)

    assert scores["glitch"] > scores["normal_a"]
    assert scores["glitch"] > scores["normal_b"]

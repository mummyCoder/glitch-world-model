from pathlib import Path

from PIL import Image

from glitch_detection.manifest import read_manifest
from glitch_detection.preprocess import preprocess_frames


def _write_frame(path: Path, value: int) -> None:
    image = Image.new("RGB", (12, 10), color=(value, value, value))
    image.save(path)


def test_preprocess_frames_creates_clips_and_manifest(tmp_path: Path):
    input_dir = tmp_path / "frames"
    input_dir.mkdir()
    for index in range(6):
        _write_frame(input_dir / f"frame_{index:03d}.png", index * 20)

    output_dir = tmp_path / "processed"
    manifest_path = preprocess_frames(
        input_path=input_dir,
        output_dir=output_dir,
        clip_length=4,
        stride=2,
        size=8,
        fps=24.0,
    )

    records = read_manifest(manifest_path)
    assert [record.clip_id for record in records] == ["frames_000000", "frames_000001"]
    assert [(record.start_frame, record.end_frame) for record in records] == [(0, 3), (2, 5)]
    assert len(list((output_dir / "clips" / "frames_000000").glob("*.png"))) == 4
    assert (output_dir / "clips" / "frames_000000" / "000000.png").exists()

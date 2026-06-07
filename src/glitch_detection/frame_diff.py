from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image

from .manifest import read_manifest
from .preprocess import IMAGE_EXTENSIONS


def load_grayscale_frame(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float32) / 255.0


def list_clip_frames(clip_dir: Path) -> list[Path]:
    frames = [
        path
        for path in clip_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(frames)


def score_clip(clip_dir: Path) -> float:
    frames = list_clip_frames(clip_dir)
    if len(frames) < 2:
        return 0.0

    diffs: list[float] = []
    previous = load_grayscale_frame(frames[0])
    for frame_path in frames[1:]:
        current = load_grayscale_frame(frame_path)
        diffs.append(float(np.mean(np.abs(current - previous))))
        previous = current
    return float(np.mean(diffs))


def score_manifest(manifest_path: Path, output_path: Path) -> Path:
    records = read_manifest(manifest_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "clip_id",
                "source",
                "clip_dir",
                "start_frame",
                "end_frame",
                "score",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "clip_id": record.clip_id,
                    "source": record.source,
                    "clip_dir": record.clip_dir,
                    "start_frame": record.start_frame,
                    "end_frame": record.end_frame,
                    "score": f"{score_clip(Path(record.clip_dir)):.8f}",
                }
            )
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score clips with a frame-difference baseline.")
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.csv.")
    parser.add_argument("--output", required=True, type=Path, help="Output scores.csv path.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_path = score_manifest(args.manifest, args.output)
    print(f"Wrote scores: {output_path}")


if __name__ == "__main__":
    main()

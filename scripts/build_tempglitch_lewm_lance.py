from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from glitch_detection.lewm_data import episode_from_video, write_lance_dataset


def _rows_by_source(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return {row["source"]: row for row in csv.DictReader(handle)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert TempGlitch videos to LeWM Lance.")
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--video-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--partition", choices=["train", "validation"], required=True)
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--image-size", type=int, default=112)
    parser.add_argument("--max-episodes", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    metadata = _rows_by_source(args.metadata)
    split = _rows_by_source(args.split)
    rows = []
    for source in metadata:
        row = split.get(source)
        if row is None:
            raise ValueError(f"Missing frozen TempGlitch split row for source {source!r}.")
        if row["split"] == args.partition and row["materialize"].lower() == "true":
            rows.append(row)
    if args.partition == "train":
        rows = [row for row in rows if row["label"] == "Normal"]
    if args.max_episodes is not None:
        rows = rows[: args.max_episodes]
    episodes = []
    for row in rows:
        metadata_row = metadata.get(row["source"])
        if metadata_row is None:
            raise ValueError(f"Missing TempGlitch metadata for source {row['source']!r}.")
        video_path = args.video_root / Path(metadata_row["local_video_path"])
        if not video_path.is_file():
            raise FileNotFoundError(f"Missing TempGlitch video: {video_path}")
        episodes.append(
            episode_from_video(
                video_path,
                dataset_id="asgaardlab/TempGlitch",
                source=row["source"],
                episode_id=row["episode_id"],
                category=row["category"],
                label=row["label"],
                split=row["split"],
                pair_id=row["pair_id"],
                frame_stride=args.frame_stride,
                image_size=args.image_size,
                max_steps=args.max_steps,
            )
        )
    write_lance_dataset(episodes, args.output)
    print(
        json.dumps(
            {
                "dataset": "tempglitch",
                "partition": args.partition,
                "episode_count": len(episodes),
                "action_mode": "zero_action",
                "action_dim": 1,
                "output": str(args.output),
                "locked_test_materialized": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

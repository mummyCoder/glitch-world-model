from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.gate6_data import read_rows_by_source, select_tempglitch_rows
from glitch_detection.lewm_data import episode_from_video, write_lance_dataset


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
    parser.add_argument("--label-filter", choices=["Normal", "Buggy"], default=None)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    metadata = read_rows_by_source(args.metadata)
    split = read_rows_by_source(args.split)
    label_filter = args.label_filter
    if label_filter is None and args.partition == "train":
        label_filter = "Normal"
    rows = select_tempglitch_rows(
        metadata,
        split,
        partition=args.partition,
        label_filter=label_filter,
        max_episodes=args.max_episodes,
        seed=args.seed,
    )
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
                "label_filter": label_filter,
                "seed": args.seed,
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

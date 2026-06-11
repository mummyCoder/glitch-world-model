from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from glitch_detection.lewm_data import episode_from_wob_tar, write_lance_dataset

DATASET_IDS = {
    "Normal": "benedictwilkinsai/world-of-bugs-normal",
    "Buggy": "benedictwilkinsai/world-of-bugs-test",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert WOB tar episodes to LeWM Lance.")
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--partition", choices=["train", "validation"], required=True)
    parser.add_argument("--max-episodes", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--action-dim", type=int, default=4)
    parser.add_argument(
        "--allow-partial-attachment",
        action="store_true",
        help="Skip frozen rows whose tar is not present in an explicitly sharded attachment.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    with args.split.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["split"] == args.partition and row["materialize"].lower() == "true"
        ]
    if args.partition == "train":
        rows = [row for row in rows if row["label"] == "Normal"]
    episodes = []
    for row in rows:
        tar_path = args.dataset_root / Path(row["source"])
        if not tar_path.is_file():
            if args.allow_partial_attachment:
                continue
            raise FileNotFoundError(f"Missing WOB episode tar: {tar_path}")
        episodes.append(
            episode_from_wob_tar(
                tar_path,
                dataset_id=DATASET_IDS[row["label"]],
                source=row["source"],
                episode_id=row["episode_id"],
                category=row["category"],
                label=row["label"],
                split=row["split"],
                pair_id=row["pair_id"],
                action_dim=args.action_dim,
                max_steps=args.max_steps,
            )
        )
        if args.max_episodes is not None and len(episodes) >= args.max_episodes:
            break
    write_lance_dataset(episodes, args.output)
    print(
        json.dumps(
            {
                "dataset": "world_of_bugs",
                "partition": args.partition,
                "episode_count": len(episodes),
                "action_mode": "real",
                "action_dim": args.action_dim,
                "output": str(args.output),
                "locked_test_materialized": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

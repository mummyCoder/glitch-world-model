from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from glitch_detection.lewm_data import episode_from_clip, write_lance_dataset
from glitch_detection.manifest import read_manifest


def _read_split(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return {row["source"]: row for row in rows}


def build_lewm_lance_dataset(
    manifest_path: Path,
    split_path: Path,
    output_path: Path,
    *,
    dataset_id: str,
    partition: str,
    action_mode: str,
    actions_root: Path | None = None,
) -> dict[str, object]:
    if partition == "test":
        raise PermissionError("Locked-test LeWM conversion requires a separate release gate.")
    split_by_source = _read_split(split_path)
    episodes = []
    for record in read_manifest(manifest_path):
        row = split_by_source.get(record.source)
        if row is None or row["split"] != partition:
            continue
        if partition == "train" and row["label"] != "Normal":
            continue
        actions = None
        if action_mode == "real":
            if actions_root is None:
                raise ValueError("Real-action conversion requires --actions-root.")
            action_path = actions_root / f"{record.clip_id}.npy"
            if not action_path.is_file():
                raise FileNotFoundError(f"Missing synchronized actions: {action_path}")
            actions = np.load(action_path)
        episodes.append(
            episode_from_clip(
                record,
                dataset_id=dataset_id,
                category=row["category"],
                label=row["label"],
                split=row["split"],
                pair_id=row.get("pair_id") or row.get("pair_id_heuristic") or record.source,
                action_mode=action_mode,
                actions=actions,
            )
        )
    write_lance_dataset(episodes, output_path)
    return {
        "dataset_id": dataset_id,
        "partition": partition,
        "action_mode": action_mode,
        "episode_count": len(episodes),
        "output_path": str(output_path),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an upstream-readable LeWM Lance dataset.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--partition", choices=["train", "validation"], required=True)
    parser.add_argument("--action-mode", choices=["real", "zero_action"], required=True)
    parser.add_argument("--actions-root", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    summary = build_lewm_lance_dataset(
        args.manifest,
        args.split,
        args.output,
        dataset_id=args.dataset_id,
        partition=args.partition,
        action_mode=args.action_mode,
        actions_root=args.actions_root,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

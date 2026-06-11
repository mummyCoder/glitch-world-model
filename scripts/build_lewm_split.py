from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from glitch_detection.lewm_protocol import assign_hashed_group_splits, write_lewm_split


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _read_exposed(path: Path | None) -> set[str]:
    if path is None:
        return set()
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return {row["pair_id"] for row in reader}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a deterministic grouped LeWM split.")
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-ratio", type=float, default=0.2)
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--exposed-groups", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    exposed = _read_exposed(args.exposed_groups)
    records = assign_hashed_group_splits(
        _read_rows(args.metadata),
        dataset_id=args.dataset_id,
        seed=args.seed,
        validation_ratio=args.validation_ratio,
        test_ratio=args.test_ratio,
        exposed_groups=exposed,
    )
    split_path, audit_path = write_lewm_split(
        args.output,
        records,
        seed=args.seed,
        exposed_groups=exposed,
    )
    print(json.dumps({"split_path": str(split_path), "audit_path": str(audit_path)}, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.pairs import pair_leakage_report
from glitch_detection.splits import assign_grouped_video_splits, validate_no_group_leakage
from glitch_detection.tempglitch import read_tempglitch_metadata

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate repeated TempGlitch pair-suspect grouped splits."
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=ROOT / "data" / "raw" / "tempglitch_phase3b" / "metadata.csv",
    )
    parser.add_argument(
        "--old-split",
        type=Path,
        default=ROOT / "data" / "processed" / "tempglitch_phase3b" / "split.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase6c" / "repeated_grouped_split_plan.json",
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--dry-run", action="store_true", default=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    metadata_rows = read_tempglitch_metadata(args.metadata)
    old_rows = []
    if args.old_split.is_file():
        import csv

        with args.old_split.open("r", newline="", encoding="utf-8-sig") as handle:
            old_rows = list(csv.DictReader(handle))

    runs = []
    for seed in args.seeds:
        records = assign_grouped_video_splits(metadata_rows, seed=seed)
        validation = validate_no_group_leakage(records)
        runs.append(
            {
                "seed": seed,
                "video_count": len(records),
                "group_count": validation["group_count"],
                "cross_split_group_count": validation["cross_split_group_count"],
                "split_counts": {
                    split: sum(record.split == split for record in records)
                    for split in ["train", "validation", "test"]
                },
            }
        )

    payload = {
        "mode": "dry-run",
        "grouping_mode": "pair_id_heuristic",
        "old_split_leakage": pair_leakage_report(old_rows) if old_rows else None,
        "runs": runs,
        "all_runs_leakage_free": all(run["cross_split_group_count"] == 0 for run in runs),
        "scoring_status": (
            "TBD: dry-run validates planned splits only; repeated refit/selection/test runs "
            "must be executed before reporting repeated-split performance."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Repeated grouped split dry-run: {len(runs)} seeds")
    print(f"All grouped splits leakage-free: {payload['all_runs_leakage_free']}")
    print(f"Plan: {args.output}")


if __name__ == "__main__":
    main()
